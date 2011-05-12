# -*- coding: utf-8 -*-
import os
import tempfile
from itertools import ifilter
from django.db import transaction, IntegrityError
from django.conf import settings
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
from transifex.projects.signals import post_submit_translation

from transifex.resources.decorators import method_decorator
from transifex.resources.models import Resource, SourceEntity, Translation, \
        RLStats
from transifex.resources.views import _compile_translation_template
from transifex.resources.formats import get_i18n_method_from_mimetype, \
        parser_for, get_file_extension_for_method, get_mimetype_from_method
from transifex.resources.formats.core import ParseError
from transifex.teams.models import Team

from transifex.api.utils import BAD_REQUEST


class BadRequestError(Exception):
    pass

class NoContentError(Exception):
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
        return get_mimetype_from_method(r.i18n_type)

    @classmethod
    def source_language_code(cls, r):
        """
        Return just the code of the source language.
        """
        return r.source_language.code

    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')
    default_fields = ('slug', 'name', 'mimetype', 'source_language', )
    details_fields = (
        'slug', 'name', 'created', 'available_languages', 'mimetype',
        'source_language_code', 'project_slug', 'wordcount', 'total_entities',
        'accept_translations', 'last_update',
    )
    fields = default_fields
    allowed_fields = (
        'slug', 'name', 'accept_translations', 'source_language',
        'mimetype', 'content',
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
            return self._create(request, project_slug, data)
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
            except Project.NotFound:
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

    def _create(self, request, project_slug, data):
        # Check for unavailable fields
        try:
            self._check_fields(data.iterkeys())
        except AttributeError, e:
            return BAD_REQUEST("Field '%s' is not allowed." % e.message)
        # Check for obligatory fields
        for field in ('name', 'slug', 'source_language', ):
            if field not in data:
                return BAD_REQUEST("Field '%s' must be specified." % field)

        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND
        slang = data.get('source_language', None)
        i18n_type = get_i18n_method_from_mimetype(data.get('mimetype', None))
        if 'application/json' in request.content_type and i18n_type is None:
            return BAD_REQUEST("Field 'mimetype' must be specified.")
        if i18n_type is not None:
            del data['mimetype']
        try:
            source_language = Language.objects.by_code_or_alias(slang)
            del data['source_language']
        except:
            return BAD_REQUEST("Language code '%s' does not exist." % slang)

        # save resource
        try:
            r = Resource(
                project=project, source_language=source_language,
            )
            r.i18n_type = i18n_type
            for key in ifilter(lambda k: k != "content", data.iterkeys()):
                setattr(r, key, data[key])
        except:
            return BAD_REQUEST("Invalid arguments given.")
        try:
            r.save()
        except IntegrityError, e:
            return BAD_REQUEST(
                "A resource with the same slug exists in this project."
            )

        # save source entities
        try:
            t = Translation.get_object("create", request, r, source_language)
        except AttributeError, e:
            r.delete()
            return BAD_REQUEST("The content type of the request is not valid.")
        try:
            res = t.create()
        except (BadRequestError, NoContentError), e:
            r.delete()
            return BAD_REQUEST(e.message)
        res = t.__class__.to_http_for_create(t, res)
        if res.status_code == 200:
            res.status_code = 201
        return res

    @require_mime('json')
    def _createv1(self, request, project_slug, resource_slug, data):
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND
        slang = data.pop('source_language', None)
        source_language = None
        try:
            source_language = Language.objects.by_code_or_alias(slang)
        except:
            pass

        if not source_language:
            return BAD_REQUEST("No source language was specified.")

        try:
            Resource.objects.get_or_create(
                project=project, source_language=source_language, **data
            )
        except:
            return BAD_REQUEST("The json you provided is misformatted.")
        return rc.CREATED

    def _update(self, request, project_slug, resource_slug):
        data = getattr(request, 'data', None)
        if not data:            # Check for {} as well
            return BAD_REQUEST("Empty request")
        try:
            self._check_fields(data.iterkeys())
        except AttributeError, e:
            return BAD_REQUEST("Field '%s' is not allowed." % e.message)

        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND
        slang = data.pop('source_language', None)
        source_language = None
        i18n_type = get_i18n_method_from_mimetype(data.pop('mimetype', None))
        if slang is not None:
            try:
                source_language = Language.objects.by_code_or_alias(slang)
            except Language.DoesNotExist:
                return BAD_REQUEST("Language code '%s' does not exist." % slang)

        try:
            resource = Resource.objects.get(slug=resource_slug)
        except Resource.DoesNotExist:
            return BAD_REQUEST("Resource %s does not exist" % resource_slug)
        try:
            for key, value in data.iteritems():
                setattr(resource, key, value)
            if source_language:
                resource.source_language = source_language
            if i18n_type is not None:
                resource.i18n_type = i18n_type
            resource.save()
        except:
            return rc.BAD_REQUEST
        return rc.ALL_OK

    def _delete(self, request, project_slug, resource_slug):
        try:
            resource = Resource.objects.get(slug=resource_slug)
        except Resource.DoesNotExist:
            return rc.NOT_FOUND
        try:
            resource.delete()
        except:
            return rc.INTERNAL_ERROR
        return rc.DELETED

    def _check_fields(self, fields):
        for field in fields:
            if not field in self.allowed_fields:
                raise AttributeError(field)


class StatsHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, project_slug, resource_slug,
             lang_code=None, api_version=1):
        """
        This is an API handler to display translation statistics for individual
        resources.
        """
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

class FileHandler(BaseHandler):
    allowed_methods = ('GET')

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
            template = _compile_translation_template(resource, language)
        except Exception, e:
            logger.error(e.message, exc_info=True)
            return BAD_REQUEST("Error compiling the translation file: %s" %e )

        i18n_method = settings.I18N_METHODS[resource.i18n_type]
        response = HttpResponse(template, mimetype=i18n_method['mimetype'])
        response['Content-Disposition'] = ('attachment; filename="%s_%s%s"' % (
        smart_unicode(resource.name), language.code,
        i18n_method['file-extensions'].split(', ')[0]))

        return response


class TranslationHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT', )

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def read(self, request, project_slug, resource_slug,
             lang_code=None, api_version=2):
        return self._read(request, project_slug, resource_slug, lang_code)

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_resource_add_change,
            (Project, 'slug__exact', 'project_slug')
    ))
    def update(self, request, project_slug, resource_slug,
               lang_code, api_version=2):
        return self._update(request, project_slug, resource_slug, lang_code)

    def _read(self, request, project_slug, resource_slug, lang_code):
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
        translation = Translation.get_object("get", request, r, language)
        res = translation.get()
        return translation.__class__.to_http_for_get(
            translation, res
        )

    def _update(self, request, project_slug, resource_slug, lang_code=None):
        # Permissions handling
        try:
            resource = Resource.objects.get(
                slug=resource_slug, project__slug=project_slug
            )
        except Resource.DoesNotExist:
            return rc.NOT_FOUND
        if lang_code == "source":
            language = resource.source_language
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
        if (not check.submit_translations(team or resource.project) or\
            not resource.accept_translations) and not\
                check.maintain(resource.project):
            return rc.FORBIDDEN

        try:
            t = Translation.get_object("create", request, resource, language)
            res = t.create()
        except BadRequestError, e:
            return BAD_REQUEST(e.message)
        except NoContentError, e:
            return BAD_REQUEST(e.message)
        except AttributeError, e:
            return BAD_REQUEST("The content type of the request is not valid.")
        return t.__class__.to_http_for_create(t, res)


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

    def __init__(self, request, resource, language=None):
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

    def get(self):
        """
        Get a translation.

        If lang_code is None, return all translations.
        """
        raise NotImplementedError

    def _parse_translation(self, parser, filename):
        strings_added, strings_updated = 0, 0
        fhandler = parser(filename=filename)
        fhandler.bind_resource(self.resource)
        fhandler.set_language(self.language)

        is_source = self.resource.source_language == self.language
        try:
            fhandler.contents_check(fhandler.filename)
            fhandler.parse_file(is_source)
            strings_added, strings_updated = fhandler.save2db(
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
        i18n_method = settings.I18N_METHODS[translation.resource.i18n_type]
        response = HttpResponse(result, mimetype=i18n_method['mimetype'])
        response['Content-Disposition'] = ('attachment; filename="%s_%s%s"' % (
                smart_unicode(translation.resource.name),
                translation.language.code,
                i18n_method['file-extensions'].split(', ')[0])
        )
        return response

    def get(self):
        """
        Return the requested translation as a file.

        Returns:
            The compiled template.

        Raises:
            BadRequestError: There was a problem with the request.
        """
        try:
            template = _compile_translation_template(
                self.resource, self.language
            )
        except Exception, e:
            logger.error(e.message, exc_info=True)
            return BadRequestError("Error compiling the translation file: %s" %e )
        return template

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

            parser = parser_for(file_.name)
            if parser is None:
                raise BadRequestError("Unknown file type")
            if size == 0:
                raise BadRequestError("Empty file")

            try:
                parser.contents_check(file_.name)
                logger.debug("Uploaded file %s" % file_.name)
            except (FileCheckError, ParseError), e:
                raise BadRequestError("Error uploading file: %s" % e.message)
            except Exception, e:
                logger.error(e.message, exc_info=True)
                raise BadRequestError("A strange error happened.")

            res = self._parse_translation(parser, file_.name)
        finally:
            os.unlink(file_.name)
        return res


class StringTranslation(Translation):
    """
    Handle requests for translation as strings.
    """

    def get(self, start=None, end=None):
        """
        Return the requested translation in a json string.

        If self.language is None, return all translations.

        Args:
            start: Start for pagination.
            end: End for pagination.

        Returns:
            A dict with the translation(s).

        Raises:
            BadRequestError: There was a problem with the request.
        """
        try:
            template = _compile_translation_template(
                self.resource, self.language
            )
        except Exception, e:
            logger.error(e.message, exc_info=True)
            raise BadRequestError(
                "Error compiling the translation file: %s" % e
            )

        i18n_method = settings.I18N_METHODS[self.resource.i18n_type]
        return {
            'content': template,
            'mimetype': i18n_method['mimetype']
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
        parser = parser_for(
            mimetype=get_mimetype_from_method(self.resource.i18n_type)
        )
        if parser is None:
            raise BadRequestError("Mimetype not supported")

        file_ = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix=get_file_extension_for_method(self.resource.i18n_type),
            delete=False,
        )
        try:
            file_.write(self.data['content'].encode('UTF-8'))
            file_.close()
            try:
                parser.contents_check(file_.name)
            except (FileCheckError, ParseError), e:
                raise BadRequestError(e.message)
            except Exception, e:
                logger.error(e.message, exc_info=True)
                raise BadequestError("A strange error has happened.")

            res = self._parse_translation(parser, file_.name)
        finally:
            os.unlink(file_.name)
        return res

