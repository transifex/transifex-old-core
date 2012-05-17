# -*- coding: utf-8 -*-

"""
API for Translation objects.
"""

from __future__ import absolute_import
from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger
from transifex.projects.permissions import *
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.projects.permissions.project import ProjectPermission
from transifex.resources.decorators import method_decorator
from transifex.resources.models import Resource, SourceEntity, Translation
from transifex.teams.models import Team
from transifex.resources.handlers import invalidate_stats_cache
from transifex.api.utils import BAD_REQUEST
from .exceptions import BadRequestError, NoContentError, NotFoundError, \
        ForbiddenError


class TranslationBaseHandler(BaseHandler):

    allowed_methods = ('GET', 'PUT', )

    def _generate_translations_dict(self, translations, field_map={},
                                    single=False):
        """
        Generate result to returned to the user for the related
        translations

        Args:
            translations: A translation values dictionary
            field_map: A dictionary mapping the keys of dictionary
                       translation to the keys used in output JSON
            single: A boolean, True if it's for SingleTranslationHandler
        Returns:
            A dictionary
        """
        result = []
        buf = {}
        for count, translation in enumerate(translations):
            d = {}
            append = True
            pluralized = False
            index = -1
            if translation.get('source_entity__pluralized'):
                if buf.get(translation.get('source_entity__id')) != None:
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

    def _get_fieldmap_and_fields(self, request):
        """
        Get fieldmap and fields from request.

        Args:
            request: An HTTP request object.
        Returns:
            A tuple, (field_map, fields) where field_map is a dictionary
            and fields is a list
        """
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

        return (field_map, fields)

    def _get_translation_query_filters(self, request, resource,
            language):
        """
        Get filters for querying Translation
        Args:
            request: An HTTP request object
            resource: A Resource object
            language: A language object
        Returns:
            A dictionary
        """

        filters = {
                'resource': resource,
                'language': language,
        }

        if request.GET.get('key'):
            filters.update({'source_entity__string__icontains': \
                    request.GET.get('key')})

        if request.GET.get('context'):
            filters.update({'source_entity__context__icontains':\
                    request.GET.get('context')})

        return filters

    def _get_objects_from_read_request_params(self, project_slug,
            resource_slug, language_code):
        """
        Get objects from read request parameters if the related objects
        exist. In case an object does not exist, then raise an error.
        If all objects are found, return a tuple of the objects.

        Args:
            project_slug: A project slug
            resource_slug: A resource slug
            language_code: A language code
        Returns:
            If objects for all parameters are found, then return
            a tuple, (project, resource, language)
            else raise an error
        """
        try:
            project = Project.objects.get(slug=project_slug)
            resource = Resource.objects.get(slug=resource_slug,
                    project=project)
            language = Language.objects.by_code_or_alias(language_code)
        except Project.DoesNotExist, e:
            raise NotFoundError("Project with slug '%s' does not exist" % \
                    project_slug)
        except Resource.DoesNotExist, e:
            raise NotFoundError("Resource '%s.%s' does not exist" % \
                    (project_slug, resource_slug))
        except Language.DoesNotExist, e:
            raise NotFoundError("Language with code '%s' does not exist." %\
                    language_code)
        return (project, resource, language)

    def _get_objects_from_update_request_params(self, project_slug,
            resource_slug, language_code):
        """
        Get objects from update request parameters if the objects
        related to the parameters exist. Raise an error if an object
        for a parameter is not found. If all objects are found, the
        return a tuple of the objects.

        Args:
            project_slug: A project slug
            resource_slug: A resource slug
            language_code: A language code
        Returns:
            If objects for all parameters are found, then return
            a tuple, (project, resource, language),
            else if language == source language, raise ForbiddenError
        """
        objs = self._get_objects_from_read_request_params(project_slug,
                resource_slug, language_code)
        if objs[2] == objs[1].source_language:
            raise ForbiddenError("Forbidden to update translations "\
                    "in source language.")
        return objs

    def _check_json_data(self, translations):
        """Check if translations exist and are inside a list.
        Else, raise an error.
        """
        if not translations:
            raise NoContentError("Translations not found!")
        if not isinstance(translations, list):
            raise BadRequestError("Translations are not in a list!")
        return True

    def _translations_as_dict(self, translations, language):
        """
        Get a dictionary where source_entity id is mapped to
        translations.

        Args:
            translations: A dictionary containing translation data
                          from request.data
            language: A Language object

        Returns:
            A dictionary
        """
        se_ids = []
        for translation in translations:
            se_id = translation.get('source_entity_id')
            if se_id:
                se_ids.append(se_id)

        trans_obj_dict = {}
        for t in Translation.objects.filter(
                source_entity__id__in=se_ids, language=language
                ).select_related('source_entity', 'user').iterator():
            if trans_obj_dict.get(t.source_entity.id):
                trans_obj_dict.get(t.source_entity.id).append(t)
            else:
                trans_obj_dict[t.source_entity.id] = [t]

        return trans_obj_dict

    def _check_user_perms(self, can_submit_translations=False,
            accept_translations=False, is_maintainer=False,
            can_review=False, translation_objs=[], translation={}):
        """
        Check if user has necessary permissions.
        Args:
            can_submit_translations: A boolean
            accept_translations: A boolean
            is_maintainer: A boolean
            can_review: A boolean
            translation_objs: A list
            translation: A translation dictionary
        Returns:
            A boolean
        """
        if (not can_submit_translations or\
            not accept_translations) and not\
                is_maintainer:
            return False
        if not translation_objs:
            return False
        reviewed = translation_objs[0].reviewed
        if (reviewed or translation.get('reviewed') != reviewed) and\
                not can_review:
            return False
        return True

    def _collect_updated_translations(self, translation, trans_obj_dict,
            se_id, updated_translations, user, pluralized):
        """
        Collect updated translations
        Args:
            translation: A dictionary representing a translation(s) in
                         request JSON
            trans_obj_dict: A dictionary mapping source_entity id to
                           translations
            se_id: An integer representing source_entity id
            updated_translations: A list of updated translations
            user: A User object
            pluaralized: A boolean
        """
        for t in trans_obj_dict.get(se_id):
            t.user = user
            if translation.has_key('reviewed'):
                t.reviewed = translation.get('reviewed')
            if pluralized:
                t.string = translation['translation'].get(str(t.rule))
            else:
                t.string = translation['translation']

            updated_translations.append(t)

    def _is_pluralized(self, translation, nplurals):
        """Check plural forms of a translation group

        Args:
            translation: A dictionary representing a translation(s) in
                         request JSON
            nplurals: A list containing plural rule numbers for a language
        Returns:
            A dictionary
            {
                'pluralized': A boolean,
                'error': A boolean
            }
        """
        result = {'pluralized': False, 'error':False}
        if isinstance(translation.get('translation'), dict):
            result['pluralized'] = True
            plural_forms = translation.get('translation').keys()
            for rule in plural_forms:
                if not translation.get('translation').get(rule).strip():
                    plural_forms.pop(rule)
            plural_forms = [int(r) for r in plural_forms]
            plural_forms.sort()
            if plural_forms != nplurals:
                result['error'] = True
        else:
            if not translation.get('translation').strip():
                result['error'] = True
        return result

    @transaction.commit_on_success
    def _update_translations(self, updated_translations):
        """Bulk update translations
        Args:
            updated_translations: A list of updated Translation objects
        """
        Translation.objects.bulk_update(updated_translations)
        transaction.commit()

    def _get_update_fieldmap_and_fields(self, keys):
        """Get fieldmap and fields for a PUT request.
        Args:
            keys: A list of dictionary keys for request.data
        Returns:
            A tuple, (dictionary, list)
        """
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

        if 'source_entity__pluralized' not in fields:
            fields.append('source_entity__pluralized')
        if 'rule' not in fields:
            fields.append('rule')

        return (field_map_, fields)


class SingleTranslationHandler(TranslationBaseHandler):
    """Read and update a single translation"""

    def _check_if_user_can_update_translation(self, project, resource,
            language, user, request_user, translations, translation_data,
            update_fields):
        """Check if user can update translations. This method
        also adds some data to update_fields.

        We use the following criteria for this:
            - request_user must be a project maintainer or
                team coordinator.
            - user must be a maintainer or a translator. If he is
                a translator, then resource must accept translations.
            - If the translations to be updated are reviewed, then
                user must have necessary permissions to review the
                translations in order to update them

        Args:
            project: A Project instance
            resource: A Resource instance
            language: A Language instance
            user: A User instance
            request_user: An User instance (request.user)
            translations: A Translation queryset
            translation_data: A dictionary (request.data),
            update_fields: A dictionary containing fields to be
                    updated in the translations.
        """
        team = Team.objects.get_or_none(project, language.code)
        if request_user not in project.maintainers.all() and not (team\
                and request_user in team.coordinators.all()):
            raise ForbiddenError("You are forbidden to update this(these) "\
                    "translation(s).")
        check = ProjectPermission(user)
        if (not check.submit_translations(team or project) or\
            not resource.accept_translations) and not\
                check.maintain(project):
            raise ForbiddenError("User '%s' is forbidden to update this "\
                    "translation for resource '%s.%s' in language '%s'."\
                    % (user.username, project.slug,
                        resource.slug, language.code))

        reviewed = translations[0].reviewed
        can_review = check.proofread(project, language)
        if (reviewed or translation_data.get('reviewed') != reviewed)\
                and not can_review:
            raise ForbiddenError("User '%s' cannot update this reviewed "\
                    "translation." % user.username)
        if isinstance(translation_data.get('reviewed'), bool):
            update_fields['reviewed'] = translation_data.get('reviewed')
        update_fields['user'] = user

    def _update_translations(self, source_entity, language, translations,
            translation_strings, update_fields):
        """Updates translations and returns a queryset for updated
        translations

        Args:
            source_entity: A SourceEntity instance
            language: A Language instance
            translations: A Translation queryset for the
                translations to be updated.
            translation_strings: A string if source_entity
                is not pluralized, else a dictionary mapping
                translation string to a plural rule.
            update_fields: A dictionary containing translation
                attributes to be updated.

        Returns:
            A queryset of Translation containing translations
            that have been updated.
        """

        if not source_entity.pluralized:
            update_fields['string']=translation_strings
            translations.filter(rule=5).update(**update_fields)
        else:
            nplurals = language.get_pluralrules_numbers()
            for rule in translation_strings.keys():
                if not translation_strings.get(rule, '').strip():
                    translation_strings.pop(rule)
            plural_forms = translation_strings.keys()
            plural_forms = [int(r) for r in plural_forms]
            plural_forms.sort()
            if nplurals != plural_forms:
                raise BadRequestError("Invalid plural forms in translation.")
            for rule in translation_strings.keys():
                update_fields['string'] = translation_strings[rule]
                translations.filter(rule=rule).update(**update_fields)
        return translations

    def _get_fieldmap_and_fields(self):
        """
        Returns a tuple (field_map, fields)

        where

        fields are used as to select fields from Translation
        queryset, and

        field_map is used to map the selected field names
        with the field names used in the JSON representation of the
        translations.
        """

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
        fields.append('rule')
        return (field_map, fields)

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def read(self, request, project_slug, resource_slug,
            language_code, source_hash, api_version=2):
        try:
            project, resource, language =\
                    self._get_objects_from_read_request_params(
                    project_slug, resource_slug, language_code)
            try:
                source_entity = SourceEntity.objects.get(string_hash=source_hash,
                        resource=resource)
            except SourceEntity.DoesNotExist, e:
                return rc.NOT_FOUND

            translations = Translation.objects.filter(
                    source_entity=source_entity, language=language)

            if not translations:
                return rc.NOT_FOUND

            field_map, fields = self._get_fieldmap_and_fields()

            return self._generate_translations_dict(
                    translations.values(*fields),
                    field_map, True)
        except NotFoundError, e:
            return rc.BAD_REQUEST(unicode(e))
        except NoContentError, e:
            return rc.BAD_REQUEST(unicode(e))
        except ForbiddenError, e:
            return rc.FORBIDDEN(unicode(e))
        except BadRequestError, e:
            return rc.BAD_REQUEST(unicode(e))

    @require_mime('json')
    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def update(self, request, project_slug, resource_slug,
            language_code, source_hash, api_version=2):
        try:
            project, resource, language = \
                    self._get_objects_from_update_request_params(project_slug,
                    resource_slug, language_code)
            try:
                source_entity = SourceEntity.objects.get(
                        string_hash=source_hash,
                        resource=resource)
            except SourceEntity.DoesNotExist, e:
                return rc.NOT_FOUND
            data = request.data
            user = data.get('user') and User.objects.get(username=data.get(
                'user')) or request.user

            translations = Translation.objects.filter(
                    source_entity=source_entity, language=language)
            if not translations:
                return rc.NOT_FOUND

            # A dictionary of translation attributes to be updated
            update_fields = {}

            self._check_if_user_can_update_translation(project, resource,
                    language, user, request.user, translations,
                    data, update_fields)

            translation_strings = data.get('translation')
            translations = self._update_translations(source_entity, language,
                    translations, translation_strings, update_fields)

            field_map, fields = self._get_fieldmap_and_fields()

            return self._generate_translations_dict(
                    translations.values(*fields),
                    field_map, True)
        except NotFoundError, e:
            return rc.BAD_REQUEST(unicode(e))
        except NoContentError, e:
            return rc.BAD_REQUEST(unicode(e))
        except ForbiddenError, e:
            return rc.FORBIDDEN(unicode(e))
        except BadRequestError, e:
            return rc.BAD_REQUEST(unicode(e))


class TranslationObjectsHandler(TranslationBaseHandler):
    """
    Read and update a set of translations in
    a language for a resource.
    """

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def read(self, request, project_slug, resource_slug,
            language_code, api_version=2):
        try:
            project, resource, language = \
                    self._get_objects_from_read_request_params(
                    project_slug, resource_slug, language_code)

            field_map, fields =\
                    self._get_fieldmap_and_fields(request)

            filters = self._get_translation_query_filters(request,
                    resource, language)

            translations = Translation.objects.filter(**filters
                    ).values(*fields)
            return self._generate_translations_dict(translations, field_map)
        except NotFoundError, e:
            return rc.BAD_REQUEST(unicode(e))
        except NoContentError, e:
            return rc.BAD_REQUEST(unicode(e))
        except ForbiddenError, e:
            return rc.FORBIDDEN(unicode(e))
        except BadRequestError, e:
            return rc.BAD_REQUEST(unicode(e))

    @require_mime('json')
    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def update(self, request, project_slug, resource_slug,
            language_code, api_version=2):
        try:
            project, resource, language = \
                    self._get_objects_from_update_request_params(
                    project_slug, resource_slug, language_code)
            translations = request.data
            self._check_json_data(translations)
            team = Team.objects.get_or_none(project, language.code)

            if request.user not in project.maintainers.all() or (team and\
                    request.user not in team.coordinators.all()):
                return rc.FORBIDDEN

            nplurals = language.get_pluralrules_numbers()
            keys = ['source_entity_id', 'key', 'context', 'translation',
                    'reviewed', 'wordcount', 'last_update', 'user',
                    'position', 'occurrences', 'pluralized']

            trans_obj_dict = self._translations_as_dict(
                    translations, language)

            updated_translations = []
            se_ids = []

            for translation in translations:
                try:
                    se_id = translation.get('source_entity_id')
                    user = translation.get('user') and \
                            User.objects.get(username=translation.get(
                                'user')) or request.user

                    check = ProjectPermission(user)
                    can_review = check.proofread(project, language)
                    can_submit_translations = check.submit_translations(
                            team or resource.project)
                    accept_translations = resource.accept_translations
                    is_maintainer = check.maintain(resource.project)

                    translation_objs = trans_obj_dict.get(se_id)

                    kwargs = {
                        'can_review': can_review,
                        'can_submit_translations': can_submit_translations,
                        'accept_translations': accept_translations,
                        'is_maintainer': is_maintainer,
                        'translation_objs': translation_objs,
                        'translation': translation
                    }

                    if not self._check_user_perms(**kwargs):
                        continue

                    is_pluralized = self._is_pluralized(translation, nplurals)
                    if is_pluralized['error']:
                        continue
                    pluralized = is_pluralized['pluralized']

                    self._collect_updated_translations(
                            translation, trans_obj_dict, se_id,
                            updated_translations, user, pluralized)

                except User.DoesNotExist, e:
                    return BAD_REQUEST(unicode(e))
                except Exception, e:
                    return BAD_REQUEST(unicode(e))
                se_ids.append(se_id)

            self._update_translations(updated_translations)
            field_map, fields = self._get_update_fieldmap_and_fields(keys)

            return self._generate_translations_dict(
                    Translation.objects.filter(
                        source_entity__id__in=se_ids,
                        language=language).values(*fields),
                    field_map)
        except NotFoundError, e:
            return rc.BAD_REQUEST(unicode(e))
        except NoContentError, e:
            return rc.BAD_REQUEST(unicode(e))
        except ForbiddenError, e:
            return rc.FORBIDDEN(unicode(e))
        except BadRequestError, e:
            return rc.BAD_REQUEST(unicode(e))
