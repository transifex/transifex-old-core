# -*- coding: utf-8 -*-
import os
import tempfile
import urllib
from itertools import ifilter
from django.db import transaction, IntegrityError, DatabaseError
from django.conf import settings
from django.forms import ValidationError
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _

from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc, throttle, require_mime

from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger
from transifex.txcommon.exceptions import FileCheckError
from transifex.txcommon.utils import paginate
from transifex.projects.permissions import *
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.projects.permissions.project import ProjectPermission
from transifex.projects.signals import post_submit_translation, post_resource_save

from transifex.resources.decorators import method_decorator
from transifex.resources.models import Resource, SourceEntity, \
        Translation as TranslationModel, RLStats
from transifex.resources.backends import ResourceBackend, FormatsBackend, \
        ResourceBackendError, content_from_uploaded_file, \
        filename_of_uploaded_file
from transifex.resources.formats import Mode
from transifex.resources.formats.registry import registry
from transifex.resources.formats.core import ParseError
from transifex.resources.formats.pseudo import get_pseudo_class
from transifex.teams.models import Team

from transifex.resources.handlers import invalidate_stats_cache

from transifex.api.utils import BAD_REQUEST


class BadRequestError(Exception):
    pass


class NoContentError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ResourceHandler(BaseHandler):
    """
    Resource Handler for CRUD operations.
    """
    @classmethod
    def project_slug(cls, sfk):
        """
        This is a work around to include the project slug in the resource API
        details, so that it is shown as a normal field.
        """
        if sfk.project:
            return sfk.project.slug
        return None

    @classmethod
    def mimetype(cls, r):
        """
        Return the mimetype in a GET request instead of the i18n_type.
        """
        return registry.mimetypes_for(r.i18n_method)[0]

    @classmethod
    def source_language_code(cls, r):
        """
        Return just the code of the source language.
        """
        return r.source_language.code

    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')
    default_fields = (
        'slug', 'name', 'i18n_type', 'source_language_code', 'category',
    )
    details_fields = (
        'slug', 'name', 'created', 'available_languages', 'i18n_type',
        'source_language_code', 'project_slug', 'wordcount', 'total_entities',
        'accept_translations', 'last_update', 'category',
    )
    fields = default_fields
    allowed_fields = (
        'slug', 'name', 'accept_translations', 'i18n_type',
        'content', 'category',
    )
    written_fields = (
        'slug', 'name', 'accept_translations', 'content', 'category',
    )

    apiv1_fields = ('slug', 'name', 'created', 'available_languages', 'i18n_type',
                    'source_language', 'project_slug')
    exclude = ()

    def read(self, request, project_slug, resource_slug=None, api_version=1):
        """
        Get details of a resource.
        """
        # Reset fields to default value
        ResourceHandler.fields = self.default_fields
        if api_version == 2:
            if "details" in request.GET:
                if resource_slug is None:
                    return rc.NOT_IMPLEMENTED
                ResourceHandler.fields = ResourceHandler.details_fields
        else:
            ResourceHandler.fields = ResourceHandler.apiv1_fields
        return self._read(request, project_slug, resource_slug)

    @method_decorator(one_perm_required_or_403(pr_resource_add_change,
        (Project, 'slug__exact', 'project_slug')))
    def create(self, request, project_slug, resource_slug=None, api_version=1):
        """
        Create new resource under project `project_slug` via POST
        """
        data = getattr(request, 'data', None)
        if api_version == 2:
            if resource_slug is not None:
                return BAD_REQUEST("POSTing to this url is not allowed.")
            if data is None:
                return BAD_REQUEST(
                    "At least parameters 'slug', 'name', 'i18n_type' "
                    "and 'source_language' must be specified,"
                    " as well as the source strings."
                )
            try:
                res = self._create(request, project_slug, data)
            except BadRequestError, e:
                return BAD_REQUEST(unicode(e))
            except NotFoundError, e:
                return rc.NOT_FOUND
            t = Translation.get_object("create", request)
            res = t.__class__.to_http_for_create(t, res)
            if res.status_code == 200:
                res.status_code = 201
            return res
        else:
            return self._createv1(request, project_slug, resource_slug, data)

    @require_mime('json')
    @method_decorator(one_perm_required_or_403(pr_resource_add_change,
        (Project, 'slug__exact', 'project_slug')))
    def update(self, request, project_slug, resource_slug=None, api_version=1):
        """
        API call to update resource details via PUT
        """
        if resource_slug is None:
            return BAD_REQUEST("No resource specified in url")
        return self._update(request, project_slug, resource_slug)

    @method_decorator(one_perm_required_or_403(pr_resource_delete,
        (Project, 'slug__exact', 'project_slug')))
    def delete(self, request, project_slug, resource_slug=None, api_version=1):
        """
        API call to delete resources via DELETE.
        """
        if resource_slug is None:
            return BAD_REQUEST("No resource provided.")
        return self._delete(request, project_slug, resource_slug)

    def _read(self, request, project_slug, resource_slug):
        if resource_slug is None:
            try:
                p = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                return rc.NOT_FOUND
            if not self._has_perm(request.user, p):
                return rc.FORBIDDEN
            return p.resources.all()
        try:
            resource = Resource.objects.get(
                slug=resource_slug, project__slug=project_slug
            )
        except Resource.DoesNotExist:
            return rc.NOT_FOUND
        if not self._has_perm(request.user, resource.project):
            return rc.FORBIDDEN
        return resource

    def _has_perm(self, user, project):
        """
        Check that the user has access to this resource.
        """
        perm = ProjectPermission(user)
        if not perm.private(project):
            return False
        return True

    @transaction.commit_on_success
    def _create(self, request, project_slug, data):
        # Check for unavailable fields
        try:
            self._check_fields(data.iterkeys(), self.allowed_fields)
        except AttributeError, e:
            msg = "Field '%s' is not allowed." % e
            logger.warning(msg)
            raise BadRequestError(msg)
        # Check for obligatory fields
        for field in ('name', 'slug', 'i18n_type', ):
            if field not in data:
                msg = "Field '%s' must be specified." % field
                logger.warning(msg)
                raise BadRequestError(msg)

        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist, e:
            logger.warning(unicode(e), exc_info=True)
            raise NotFoundError(unicode(e))

        # In multipart/form-encode request variables have lists
        # as values. So we use __getitem__ isntead of pop, which returns
        # the last value
        method = data['i18n_type']; del data['i18n_type']
        if not registry.is_supported(method):
            msg = "i18n_type %s is not supported." % method
            logger.warning(msg)
            raise BadRequestError(msg)
        try:
            slug = data['slug']; del data['slug']
            name = data['name']; del data['name']
            # TODO for all fields
        except KeyError, e:
            msg = "Required field is missing: %s" % e
            logger.warning(msg)
            raise BadRequestError(msg)
        if len(slug) > 50:
            raise BadRequestError(
                "The value for slug is too long. It should be less than "
                "50 characters."
            )

        try:
            content = self._get_content(request, data)
            filename = self._get_filename(request, data)
        except NoContentError, e:
            raise BadRequestError(unicode(e))

        try:
            rb = ResourceBackend()
            rb_create =  rb.create(
                project, slug, name, method, project.source_language, content,
                extra_data={'filename': filename}
            )
            post_resource_save.send(sender=None, instance=Resource.objects.get(
                slug=slug, project=project),
                    created=True, user=request.user)
            return rb_create
        except ResourceBackendError, e:
            raise BadRequestError(unicode(e))

    @require_mime('json')
    def _createv1(self, request, project_slug, resource_slug, data):
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND
        slang = data.pop('source_language', None)
        source_language = None

        if not source_language:
            return BAD_REQUEST("No or wrong source language was specified.")

        try:
            r, created = Resource.objects.get_or_create(
                project=project, **data
            )
            r.full_clean()

            if created:
                post_resource_save.send(sender=None, instance=r,
                        created=created, user=request.user)

        except ValidationError, e:
            return BAD_REQUEST("Invalid arguments given: %s" % unicode(e))
        except:
            return BAD_REQUEST("The json you provided is misformatted.")
        return rc.CREATED

    def _update(self, request, project_slug, resource_slug):
        data = getattr(request, 'data', None)
        if not data:            # Check for {} as well
            return BAD_REQUEST("Empty request")
        try:
            self._check_fields(data.iterkeys(), self.written_fields)
        except AttributeError, e:
            return BAD_REQUEST("Field '%s' is not allowed." % e)

        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND
        i18n_type = data.pop('i18n_type', None)

        try:
            resource = Resource.objects.get(project=project, slug=resource_slug)
        except Resource.DoesNotExist:
            return BAD_REQUEST("Resource %s does not exist" % resource_slug)
        try:
            for key, value in data.iteritems():
                setattr(resource, key, value)
            # if i18n_type is not None:
            #     resource.i18n_method = i18n_typ
            resource.full_clean()
            resource.save()
        except:
            return rc.BAD_REQUEST
        return rc.ALL_OK

    def _delete(self, request, project_slug, resource_slug):
        try:
            resource = Resource.objects.get(
                slug=resource_slug, project__slug=project_slug
            )
        except Resource.DoesNotExist:
            return rc.NOT_FOUND
        try:
            resource.delete()
        except:
            return rc.INTERNAL_ERROR
        return rc.DELETED

    def _check_fields(self, fields, allowed_fields):
        for field in fields:
            if not field in allowed_fields:
                raise AttributeError(field)

    def _get_content(self, request, data):
        """Get the content from the request.

        If it is file-based, return the contents of the file.

        Args:
            request: The django request object.
        Returns:
            The content of the string/file.
        """
        if 'application/json' in request.content_type:
            try:
                return data['content']
            except KeyError, e:
                msg = "No content provided"
                logger.warning(msg)
                raise NoContentError(msg)
        elif 'multipart/form-data' in request.content_type:
            if not request.FILES:
                msg = "No file has been uploaded."
                logger.warning(msg)
                raise NoContentError(msg)
            return content_from_uploaded_file(request.FILES)
        else:
            msg = "No content or file found"
            logger.warning(msg)
            raise NoContentError(msg)

    def _get_filename(self, request, data):
        """Get the filename of the uploaded file.

        Returns:
            The filename or None, if the request used json.
        """
        if 'application/json' in request.content_type:
            return None
        elif 'multipart/form-data' in request.content_type:
            if not request.FILES:
                msg = "No file has been uploaded."
                logger.warning(msg)
                raise NoContentError(msg)
            return filename_of_uploaded_file(request.FILES)
        else:
            msg = "No content or file found"
            logger.warning(msg)
            raise NoContentError(msg)



class StatsHandler(BaseHandler):
    allowed_methods = ('GET', )

    def read(self, request, project_slug, resource_slug,
             lang_code=None, api_version=1):
        """
        This is an API handler to display translation statistics for individual
        resources.
        """
        if api_version == 2:
            return self._get_stats(request=request, pslug=project_slug,
            rslug=resource_slug, lang_code=lang_code)

        # API v1 code
        try:
            resource = Resource.objects.get( project__slug = project_slug,
                slug= resource_slug)
        except Resource.DoesNotExist:
            return BAD_REQUEST("Unknown resource %s" % resource_slug)

        language = None
        if lang_code:
            try:
                language = Language.objects.by_code_or_alias(lang_code)
            except Language.DoesNotExist:
                return BAD_REQUEST("Unknown language %s" % lang_code)


        stats = RLStats.objects.by_resource(resource)
        # TODO: If we're gonna use this as a generic stats generator, we should
        # include more info in the json.
        if language:
            retval = {}
            for stat in stats.by_language(language):
                retval.update({stat.language.code:{"completed": "%s%%" %
                    (stat.translated_perc),
                    "translated_entities": stat.translated, "last_update":
                    stat.last_update}})
        else:
            retval = []
            for stat in stats:
                retval.append({stat.language.code:{"completed": "%s%%" %
                    (stat.translated_perc),
                    "translated_entities": stat.translated}})
        return retval

    def _get_stats(self, request, pslug, rslug, lang_code):
        try:
            resource = Resource.objects.get(project__slug=pslug, slug=rslug)
        except Resource.DoesNotExist, e:
            logger.debug(
                "Resource %s.%s requested, but it does not exist" % (pslug, rslug),
                exc_info=True
            )
            return rc.NOT_FOUND
        language = None
        if lang_code is not None:
            try:
                language = Language.objects.by_code_or_alias(lang_code)
            except Language.DoesNotExist, e:
                logger.debug(
                    "Language %s was requested, but it does not exist." % lang_code,
                    exc_info=True
                )
                return BAD_REQUEST("Unknown language code %s" % lang_code)

        stats = RLStats.objects.by_resource(resource)
        if language is not None:
            stat = stats.by_language(language)[0]
            return {
                'completed': '%s%%' % stat.translated_perc,
                'translated_entities': stat.translated,
                'translated_words': stat.translated_wordcount,
                'untranslated_entities': stat.untranslated,
                'untranslated_words': stat.untranslated_wordcount,
                'last_update': stat.last_update,
                'last_commiter': stat.last_committer.username if stat.last_committer else '',
                'reviewed': stat.reviewed,
                'reviewed_percentage': '%s%%' % stat.reviewed_perc,
            }
        # statistics requested for all languages
        res = {}
        for stat in stats:
            res[stat.language.code] = {
                    'completed': '%s%%' % stat.translated_perc,
                    'translated_entities': stat.translated,
                    'translated_words': stat.translated_wordcount,
                    'untranslated_entities': stat.untranslated,
                    'untranslated_words': stat.untranslated_wordcount,
                    'last_update': stat.last_update,
                    'last_commiter': stat.last_committer.username if stat.last_committer else '',
                    'reviewed': stat.reviewed,
                    'reviewed_percentage': '%s%%' % stat.reviewed_perc,
            }
        return res

class FileHandler(BaseHandler):
    allowed_methods = ('GET', 'DELETE', )

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(pr_project_private_perm,
        (Project, 'slug__exact', 'project_slug')))
    def read(self, request, project_slug, resource_slug=None,
             language_code=None, api_version=1):
        """
        API Handler to export translation files from the database
        """
        try:
            resource = Resource.objects.get(
                project__slug=project_slug, slug=resource_slug
            )
            language = Language.objects.by_code_or_alias(code=language_code)
        except (Resource.DoesNotExist, Language.DoesNotExist), e:
            return BAD_REQUEST("%s" % e )

        try:
            fb = FormatsBackend(resource, language)
            template = fb.compile_translation(None)
        except Exception, e:
            logger.error(unicode(e), exc_info=True)
            return BAD_REQUEST("Error compiling the translation file: %s" %e )

        response = HttpResponse(
            template, mimetype=registry.mimetypes_for(resource.i18n_method)[0]
        )
        response['Content-Disposition'] = (
            'attachment; filename*="UTF-8\'\'%s_%s%s"' % (
                urllib.quote(resource.name.encode('UTF-8')), language.code,
                registry.file_extension_for(resource, language)
            )
        )

        return response

    @method_decorator(one_perm_required_or_403(
            pr_resource_translations_delete,
            (Project, "slug__exact", "project_slug")))
    def delete(self, request, project_slug, resource_slug=None,
               language_code=None, api_version=1):
        """
        DELETE requests for translations.
        """
        try:
            resource = Resource.objects.get(
                slug=resource_slug, project__slug=project_slug
            )
        except Resource.DoesNotExist, e:
            return rc.NOT_FOUND

        # Error message to use in case user asked to
        # delete the source translation
        source_error_msg = "You cannot delete the translation in the" \
                " source language."
        try:
            language = Language.objects.by_code_or_alias(language_code)
        except Language.DoesNotExist:
            return rc.NOT_FOUND
        if language == resource.source_language:
            return BAD_REQUEST(source_error_msg)
        if language not in resource.available_languages:
            return rc.NOT_FOUND

        t = Translation.get_object("delete", request, resource, language)
        t.delete()
        return rc.DELETED


class SingleTranslationHandler(BaseHandler):
    """Read and update a single translation"""
    allowed_methods = ('GET', 'PUT')

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def read(self, request, project_slug, resource_slug,
            language_code, source_hash, api_version=2):
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist, e:
            return rc.NOT_FOUND
        try:
            resource = Resource.objects.get(slug=resource_slug,
                    project=project)
        except Resource.DoesNotExist, e:
            return rc.NOT_FOUND
        try:
            source_entity = SourceEntity.objects.get(string_hash=source_hash,
                    resource=resource)
        except SourceEntity.DoesNotExist, e:
            return rc.NOT_FOUND
        try:
            language = Language.objects.by_code_or_alias(language_code)
        except Language.DoesNotExist, e:
            return rc.NOT_FOUND

        translations = TranslationModel.objects.filter(
                source_entity=source_entity, language=language)

        if not translations:
            return rc.NOT_FOUND

        field_map = {
                'source_entity__id': 'source_entity_id',
                'source_entity__string': 'key',
                'source_entity__context': 'context',
                'string': 'translation',
                'reviewed': 'reviewed',
                'wordcount': 'wordcount',
                'last_update': 'last_update',
                'user__username': 'user',
                'source_entity__position': 'position',
                'source_entity__occurrences': 'occurrences',
                'source_entity__pluralized': 'pluralized'
        }

        fields = field_map.keys()

        return _generate_translations_dict(
                translations.values(*fields),
                field_map, True)

    @require_mime('json')
    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def update(self, request, project_slug, resource_slug,
            language_code, source_hash, api_version=2):
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist, e:
            return rc.NOT_FOUND
        try:
            resource = Resource.objects.get(slug=resource_slug,
                    project=project)
        except Resource.DoesNotExist, e:
            return rc.NOT_FOUND
        try:
            source_entity = SourceEntity.objects.get(string_hash=source_hash,
                    resource=resource)
        except SourceEntity.DoesNotExist, e:
            return rc.NOT_FOUND
        try:
            language = Language.objects.by_code_or_alias(language_code)
        except Language.DoesNotExist, e:
            return rc.NOT_FOUND

        if language == source_entity.resource.source_language:
            return rc.FORBIDDEN
        data = request.data
        user = data.get('user') and User.objects.get(username=data.get(
            'user')) or request.user

        team = Team.objects.get_or_none(project, language.code)
        check = ProjectPermission(user)
        if (not check.submit_translations(team or resource.project) or\
            not resource.accept_translations) and not\
                check.maintain(resource.project):
            return rc.FORBIDDEN

        translations = TranslationModel.objects.filter(
                source_entity=source_entity, language=language)

        if not translations:
            return rc.NOT_FOUND

        reviewed = translations[0].reviewed

        update_fields = {}
        if check.proofread(project, language):
            if data.get('reviewed') != None:
                update_fields['reviewed'] = data.get('reviewed')
        else:
            if reviewed:
                return rc.FORBIDDEN

        translation_strings = data.get('translation')

        update_fields['user'] = user

        if not source_entity.pluralized:
            update_fields['string']=translation_strings
            translations.filter(rule=5).update(**update_fields)
        else:
            nplurals = language.get_pluralrules_numbers()
            for rule in translation_strings.keys():
                if not translation_strings.get(rule, '').strip():
                    translation_strings.pop(rule)
            plural_forms = translation_strings.keys()
            plural_forms.sort()
            if nplurals != plural_forms:
                return rc.BAD_REQUEST
            for rule in translation_strings.keys():
                update_fields['string'] = translation_strings[rule]
                translations.filter(rule=rule).update(**update_fields)

        field_map = {
                'source_entity__id': 'source_entity_id',
                'source_entity__string': 'key',
                'source_entity__context': 'context',
                'string': 'translation',
                'reviewed': 'reviewed',
                'wordcount': 'wordcount',
                'last_update': 'last_update',
                'user__username': 'user',
                'source_entity__position': 'position',
                'source_entity__occurrences': 'occurrences',
                'source_entity__pluralized': 'pluralized'
        }

        fields = field_map.keys()

        return _generate_translations_dict(
                translations.values(*fields),
                field_map, True)


def _generate_translations_dict(translations, field_map={}, single=False):
    """Generate result to returned to the user for the related translations"""
    result = []
    buf = {}
    for count, translation in enumerate(translations):
        d = {}
        append = True
        pluralized = False
        index = -1
        if translation.get('source_entity__pluralized'):
            if buf.get(translation.get('source_entity__id')):
                index = buf.get(translation.get('source_entity__id'))
                d = result[index]
                append = False
            else:
                buf[translation.get('source_entity__id')] = count
            pluralized = True
        for key in field_map.keys():
            if pluralized:
                if key == 'string':
                    if append:
                        d[field_map[key]] = {translation['rule']:\
                                translation['string']}
                    else:
                        d[field_map[key]][translation['rule']] =\
                                translation['string']
                elif key == 'wordcount':
                    if append:
                        d[field_map[key]] = translation['wordcount']
                    else:
                        d[field_map[key]] += translation['wordcount']
                else:
                    d[field_map[key]] = translation[key]
            else:
                d[field_map[key]] = translation[key]

        if append:
            result.append(d)
        else:
           result[index] = d
    if single:
        if result:
            result = result[0]
        else:
            result = ""
    return result

class TranslationObjectsHandler(BaseHandler):
    """
    Read and update a set of translations in
    a language for a resource.
    """
    allowed_methods = ('GET', 'PUT')

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def read(self, request, project_slug, resource_slug,
            language_code, api_version=2):
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist, e:
            return rc.NOT_FOUND
        try:
            resource = Resource.objects.get(slug=resource_slug)
        except Resource.DoesNotExist, e:
            return rc.NOT_FOUND
        try:
            language = Language.objects.by_code_or_alias(language_code)
        except Language.DoesNotExist, e:
            return rc.NOT_FOUND

        fields = [
                'source_entity__id', 'source_entity__string',
                'source_entity__context', 'string',
                'source_entity__pluralized',
                'rule',
        ]

        field_map = {
                'source_entity__id': 'source_entity_id',
                'source_entity__string': 'key',
                'source_entity__context': 'context',
                'string': 'translation',
        }

        if request.GET.has_key('details'):
            fields.extend([
                'reviewed', 'wordcount', 'last_update', 'user__username',
                'source_entity__position', 'source_entity__occurrences',
            ])
            field_map.update({
                'reviewed': 'reviewed',
                'wordcount': 'wordcount',
                'last_update': 'last_update',
                'user__username': 'user',
                'source_entity__position': 'position',
                'source_entity__occurrences': 'occurrences',
                'source_entity__pluralized': 'pluralized'
            })

        filters = {
                'resource': resource,
                'language': language,
        }

        if request.GET.get('key'):
            filters.update({'source_entity__string__contains': \
                    request.GET.get('key')})

        if request.GET.get('context'):
            filters.update({'source_entity__context__contains':\
                    request.GET.get('context')})

        translations = TranslationModel.objects.filter(**filters
                ).values(*fields)
        return _generate_translations_dict(translations, field_map)


    @require_mime('json')
    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def update(self, request, project_slug, resource_slug,
            language_code, api_version=2):
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist, e:
            return rc.NOT_FOUND
        try:
            resource = Resource.objects.get(slug=resource_slug)
        except Resource.DoesNotExist, e:
            return rc.NOT_FOUND
        try:
            language = Language.objects.by_code_or_alias(language_code)
        except Language.DoesNotExist, e:
            return rc.NOT_FOUND

        team = Team.objects.get_or_none(project, language.code)

        if language == resource.source_language:
            return rc.FORBIDDEN

        translations = request.data
        if not translations:
            return rc.NOT_FOUND
        if not isinstance(translations, list):
            return rc.BAD_REQUEST

        nplurals = language.get_pluralrules_numbers()
        keys = translations[0].keys()

        se_ids = []
        for translation in translations:
            se_id = translation.get('source_entity_id')
            if se_id:
                se_ids.append(se_id)

        trans_obj_dict = {}
        for t in TranslationModel.objects.filter(
                source_entity__id__in=se_ids, language=language
                ).select_related('source_entity', 'user').iterator():
            if trans_obj_dict.get(t.source_entity.id):
                trans_obj_dict.get(t.source_entity.id).append(t)
            else:
                trans_obj_dict[t.source_entity.id] = [t]

        updated_translations = []
        se_ids = []

        for translation in translations:
            try:
                se_id = translation.get('source_entity_id')
                user = translation.get('user') and \
                        User.objects.get(trasnlation.get('user')) or\
                        request.user

                check = ProjectPermission(user)
                if (not check.submit_translations(team or resource.project) or\
                    not resource.accept_translations) and not\
                        check.maintain(resource.project):
                    continue
                if isinstance(translation.get('translation'), dict):
                    pluralized = True
                    plural_forms = translation.get('translation').keys()
                    plural_forms.sort()
                    for rule in plural_forms:
                        if translation.get('translation').get(rule).strip():
                            plural_forms.pop(rule)
                    if plural_forms != nplurals:
                        continue
                else:
                    pluralized = False
                    if not translation.get('translation').strip():
                        continue

                translation_objs = trans_obj_dict.get(se_id)
                if not translation_objs:
                    continue
                reviewed = translation_objs[0].reviewed
                review_perm = check.proofread(project, language)
                if reviewed and not review_perm:
                    continue

                for t in trans_obj_dict.get(se_id):
                    t.user = user
                    if translation.has_key('reviewed'):
                        t.reviewed = translation.get('reviewed')
                    if pluralized:
                        t.string = translation['translation'].get(t.rule)
                    else:
                        t.string = translation['translation']

                    updated_translations.append(t)

            except User.DoesNotExist:
                continue
            except:
                return rc.BAD_REQUEST
            se_ids.append(se_id)

        TranslationModel.objects.bulk_update(updated_translations)


        field_map = {
                'source_entity__id': 'source_entity_id',
                'source_entity__string': 'key',
                'source_entity__context': 'context',
                'string': 'translation',
                'reviewed': 'reviewed',
                'wordcount': 'wordcount',
                'last_update': 'last_update',
                'user__username': 'user',
                'source_entity__position': 'position',
                'source_entity__occurrences': 'occurrences',
                'source_entity__pluralized': 'pluralized'
        }

        fields = []
        field_map_ = {}
        for f in field_map.viewitems():
            if f[1] in keys:
                fields.append(f[0])
                field_map_[f[0]] = f[1]

        return _generate_translations_dict(
                TranslationModel.objects.filter(source_entity__id__in=se_ids,
                    language=language).values(*fields),
                field_map_)




class TranslationHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT', 'DELETE',)

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def read(self, request, project_slug, resource_slug,
             lang_code=None, is_pseudo=None, api_version=2):
        return self._read(request, project_slug, resource_slug, lang_code, is_pseudo)

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    def update(self, request, project_slug, resource_slug,
               lang_code, api_version=2):
        return self._update(request, project_slug, resource_slug, lang_code)

    @method_decorator(one_perm_required_or_403(
            pr_resource_translations_delete,
            (Project, "slug__exact", "project_slug")))
    def delete(self, request, project_slug, resource_slug,
               lang_code=None, api_version=2):
        return self._delete(request, project_slug, resource_slug, lang_code)

    def _read(self, request, project_slug, resource_slug, lang_code, is_pseudo):
        try:
            r = Resource.objects.get(
                slug=resource_slug, project__slug=project_slug
            )
        except Resource.DoesNotExist:
            return rc.NOT_FOUND

        if lang_code == "source":
            language = r.source_language
        else:
            try:
                language = Language.objects.by_code_or_alias(lang_code)
            except Language.DoesNotExist:
                return rc.NOT_FOUND

        # Check whether the request asked for a pseudo file, if so check if
        # a ``pseudo_type`` GET var was passed with a valid pseudo type.
        if is_pseudo:
            ptype = request.GET.get('pseudo_type', None)
            if not ptype in settings.PSEUDO_TYPES.keys():
                return rc.NOT_FOUND
            # Instantiate Pseudo type object
            pseudo_type = get_pseudo_class(ptype)(r.i18n_type)
        else:
            pseudo_type = None

        # Get the mode the user requested, if any
        mode = request.GET.get('mode', None)
        if mode is not None:
            try:
                mode = getattr(Mode, mode.upper())
            except AttributeError, e:
                return BAD_REQUEST(unicode(e))

        translation = Translation.get_object("get", request, r, language)
        try:
            res = translation.get(pseudo_type=pseudo_type, mode=mode)
        except BadRequestError, e:
            return BAD_REQUEST(unicode(e))
        except FormatsBackendError, e:
            return BAD_REQUEST(unicode(e))
        return translation.__class__.to_http_for_get(
            translation, res
        )

    def _update(self, request, project_slug, resource_slug, lang_code=None):
        # Permissions handling
        try:
            resource = Resource.objects.select_related('project').get(
                slug=resource_slug, project__slug=project_slug
            )
        except Resource.DoesNotExist:
            return rc.NOT_FOUND
        source_push = False
        if lang_code == "source":
            language = resource.source_language
            source_push = True
        else:
            try:
                language =  Language.objects.by_code_or_alias(lang_code)
            except Language.DoesNotExist:
                logger.error("Weird! Selected language code (%s) does "
                             "not match with any language in the database."
                             % lang_code)
                return BAD_REQUEST(
                    "Selected language code (%s) does not match with any"
                    "language in the database." % lang_code
                )

        team = Team.objects.get_or_none(resource.project, lang_code)
        check = ProjectPermission(request.user)
        if source_push and not check.maintain(resource.project):
            return rc.FORBIDDEN
        elif (not check.submit_translations(team or resource.project) or\
            not resource.accept_translations) and not\
                check.maintain(resource.project):
            return rc.FORBIDDEN

        try:
            t = Translation.get_object("create", request, resource, language)
            res = t.create()
        except BadRequestError, e:
            return BAD_REQUEST(unicode(e))
        except NoContentError, e:
            return BAD_REQUEST(unicode(e))
        except AttributeError, e:
            return BAD_REQUEST("The content type of the request is not valid.")
        return t.__class__.to_http_for_create(t, res)

    def _delete(self, request, project_slug, resource_slug, lang_code):
        try:
            resource = Resource.objects.get(
                slug=resource_slug, project__slug=project_slug
            )
        except Resource.DoesNotExist, e:
            return rc.NOT_FOUND

        # Error message to use in case user asked to
        # delete the source translation
        source_error_msg = "You cannot delete the translation in the" \
                " source language."
        if lang_code == 'source':
            return BAD_REQUEST(source_error_msg)
        try:
            language = Language.objects.by_code_or_alias(lang_code)
        except Language.DoesNotExist:
            return rc.NOT_FOUND
        if language == resource.source_language:
            return BAD_REQUEST(source_error_msg)
        if language not in resource.available_languages:
            return rc.NOT_FOUND

        t = Translation.get_object("delete", request, resource, language)
        t.delete()
        return rc.DELETED


class Translation(object):
    """
    Handle a translation for a resource.
    """

    @staticmethod
    def get_object(type_, request, *args):
        """
        Factory method to get the suitable object for the request.
        """
        if type_ == "get":
            if 'file' in request.GET:
                return FileTranslation(request, *args)
            else:
                return StringTranslation(request, *args)
        elif type_ == "create":
            if request.content_type == "application/json":
                return StringTranslation(request, *args)
            elif "multipart/form-data" in request.content_type:
                return FileTranslation(request, *args)
        elif type_ == "delete":
            return Translation(request, *args)
        return None


    @classmethod
    def _to_http_response(cls, translation, result,
                          status=200, mimetype='application/json'):
        return HttpResponse(result, status=status, mimetype=mimetype)

    @classmethod
    def to_http_for_get(cls, translation, result):
        """
        Return the result to a suitable HttpResponse for a GET request.

        Args:
            translation: The translation object.
            result: The result to convert to a HttpResponse.

        Returns:
            A HttpResponse with the result.
        """
        return cls._to_http_response(translation, result, status=200)

    @classmethod
    def to_http_for_create(cls, translation, result):
        """
        Return the result to a suitable HttpResponse for a PUT/POST request.

        Args:
            translation: The translation object.
            result: The result to convert to a HttpResponse.

        Returns:
            A HttpResponse with the result.
        """
        return cls._to_http_response(translation, result, status=200)

    def __init__(self, request, resource=None, language=None):
        """
        Initializer.

        Args:
            request: The request
            resource: The resource the translation is asked for.
            language: The language of the requested translation.

        """
        self.request = request
        self.data = getattr(request, 'data', 'None')
        self.resource = resource
        self.language = language

    def create(self):
        """
        Create a new translation.
        """
        raise NotImplementedError

    @transaction.commit_on_success
    def delete(self):
        """
        Delete a specific translation.

        Delete all Translation objects that belong to the specified resource
        and are in the specified language.
        """
        TranslationModel.objects.filter(
            resource=self.resource,
            language=self.language
        ).delete()
        invalidate_stats_cache(
            self.resource, self.language, user=self.request.user
        )

    def get(self, pseudo_type, mode=None):
        """Get a translation.

        Args:
            pseudo_type: The pseudo_type to use, if any.
            mode: The mode of compilation, if any.
        """
        raise NotImplementedError

    def _parse_translation(self, parser):
        """
        Parses a source/translation file.

        We assume the content has been checked for validity
        by now.
        """
        strings_added, strings_updated = 0, 0
        parser.bind_resource(self.resource)
        parser.set_language(self.language)

        is_source = self.resource.source_language == self.language
        try:
            parser.parse_file(is_source)
            strings_added, strings_updated = parser.save2db(
                is_source, user=self.request.user
            )
        except Exception, e:
            raise BadRequestError("Could not import file: %s" % e)

        messages = []
        if strings_added > 0:
            messages.append(_("%i strings added") % strings_added)
        if strings_updated > 0:
            messages.append(_("%i strings updated") % strings_updated)
        retval= {
            'strings_added': strings_added,
            'strings_updated': strings_updated,
            'redirect': reverse(
                'resource_detail',
                args=[self.resource.project.slug, self.resource.slug]
            )
        }
        logger.debug("Extraction successful, returning: %s" % retval)

        # If any string added/updated
        if retval['strings_added'] > 0 or retval['strings_updated'] > 0:
            modified = True
        else:
            modified=False
        post_submit_translation.send(
            None, request=self.request, resource=self.resource,
            language=self.language, modified=modified
        )

        return retval


class FileTranslation(Translation):
    """
    Handle requests for translation as files.
    """

    @classmethod
    def to_http_for_get(cls, translation, result):
        response = HttpResponse(
            result, mimetype=registry.mimetypes_for(
                translation.resource.i18n_method
            )[0]
        )
        response['Content-Disposition'] = (
            'attachment; filename*="UTF-8\'\'%s_%s%s"' % (
                urllib.quote(translation.resource.name.encode('UTF-8')),
                translation.language.code,
                registry.file_extension_for(
                    translation.resource, translation.language
                )
            )
        )
        return response

    def get(self, pseudo_type, mode=None):
        """
        Return the requested translation as a file.

        Returns:
            The compiled template.

        Raises:
            BadRequestError: There was a problem with the request.
        """
        try:
            fb = FormatsBackend(self.resource, self.language)
            return fb.compile_translation(pseudo_type, mode=mode)
        except Exception, e:
            logger.error(unicode(e), exc_info=True)
            raise BadRequestError("Error compiling the translation file: %s" %e )

    def create(self):
        """
        Creates a new translation from file.

        Returns:
            A dict with information for the translation.

        Raises:
            BadRequestError: There was a problem with the request.
            NoContentError: There was no file in the request.
        """
        if not self.request.FILES:
            raise NoContentError("No file has been uploaded.")

        submitted_file = self.request.FILES.values()[0]
        name = str(submitted_file.name)
        size = submitted_file.size

        try:
            file_ = tempfile.NamedTemporaryFile(
                mode='wb',
                suffix=name[name.rfind('.'):],
                delete=False
            )
            for chunk in submitted_file.chunks():
                file_.write(chunk)
            file_.close()

            parser = registry.appropriate_handler(
                self.resource,
                language=self.language,
                filename=name
            )
            parser.bind_file(file_.name)
            if parser is None:
                raise BadRequestError("Unknown file type")
            if size == 0:
                raise BadRequestError("Empty file")

            try:
                parser.is_content_valid()
                logger.debug("Uploaded file %s" % file_.name)
            except (FileCheckError, ParseError), e:
                raise BadRequestError("Error uploading file: %s" % e)
            except Exception, e:
                logger.error(unicode(e), exc_info=True)
                raise BadRequestError("A strange error happened.")

            parser.bind_file(file_.name)
            res = self._parse_translation(parser)
        finally:
            os.unlink(file_.name)
        return res


class StringTranslation(Translation):
    """
    Handle requests for translation as strings.
    """

    def get(self, start=None, end=None, pseudo_type=None, mode=None):
        """
        Return the requested translation in a json string.

        If self.language is None, return all translations.

        Args:
            start: Start for pagination.
            end: End for pagination.
            pseudo_type: The pseudo_type requested.
            mode: The mode for the compilation.
        Returns:
            A dict with the translation(s).
        Raises:
            BadRequestError: There was a problem with the request.
        """
        try:
            fb = FormatsBackend(self.resource, self.language)
            template = fb.compile_translation(pseudo_type, mode=mode)
        except Exception, e:
            logger.error(unicode(e), exc_info=True)
            raise BadRequestError(
                "Error compiling the translation file: %s" % e
            )

        if self.resource.i18n_method == 'PROPERTIES':
            template = template.decode('ISO-8859-1')
        return {
            'content': template,
            'mimetype': registry.mimetypes_for(self.resource.i18n_method)[0]
        }

    def create(self):
        """
        Create a new translation supplied as a string.

        Returns:
            A dict with information for the request.

        Raises:
            BadRequestError: There was a problem with the request.
            NoContentError: There was no content string in the request.
        """
        if 'content' not in self.data:
            raise NoContentError("No content found.")
        parser = registry.appropriate_handler(
            self.resource, language=self.language
        )
        if parser is None:
            raise BadRequestError("I18n type is not supported: %s" % i18n_type)

        file_ = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix=registry.extensions_for(self.resource.i18n_method)[0],
            delete=False,
        )
        try:
            file_.write(self.data['content'].encode('UTF-8'))
            file_.close()
            try:
                parser.bind_file(file_.name)
                parser.is_content_valid()
            except (FileCheckError, ParseError), e:
                raise BadRequestError(unicode(e))
            except Exception, e:
                logger.error(unicode(e), exc_info=True)
                raise BadRequestError("A strange error has happened.")

            parser.bind_file(file_.name)
            res = self._parse_translation(parser)
        finally:
            os.unlink(file_.name)
        return res

class FormatsHandler(BaseHandler):
    """
    Formats Handler for READ operation.
    """
    allowed_methods = ('GET',)

    def read(self, request, api_version=1):
        """
        Get details of supported i18n formats.
        """
        return registry.available_methods
