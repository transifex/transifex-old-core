# -*- coding: utf-8 -*-
from uuid import uuid4
from django.db import transaction
from django.conf import settings
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.utils.encoding import smart_unicode

from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc, throttle

from txcommon.decorators import one_perm_required_or_403
from txcommon.log import logger
from projects.permissions import *
from languages.models import Language
from projects.models import Project
from storage.models import StorageFile

from resources.decorators import method_decorator
from resources.models import Resource, SourceEntity, Translation
from resources.stats import ResourceStatsList
from resources.views import _compile_translation_template

from transifex.api.utils import BAD_REQUEST

class ResourceHandler(BaseHandler):
    """
    Resource Handler for CRUD operations.
    """

    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')
    model = Resource
    fields = ('slug', 'name', 'created', 'available_languages')
    exclude = ()

    def read(self, request, project_slug, resource_slug=None):
        """
        Get details of a resource.
        """
        if resource_slug:
            try:
                resource = Resource.objects.get(slug=resource_slug)
            except Resource.DoesNotExist:
                return rc.NOT_FOUND
            return resource
        else:
            return Resource.objects.filter(project__slug=project_slug)

    @method_decorator(one_perm_required_or_403(pr_resource_add_change,
        (Project, 'slug__exact', 'project_slug')))
    def create(self, request, project_slug, resource_slug=None):
        """
        Create new resource under project `project_slug` via POST
        """
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND

        if 'application/json' in request.content_type: # we got JSON
            data = getattr(request, 'data', None)
            slang = data.pop('source_language', None)
            source_language = None
            try:
                source_language = Language.objects.by_code_or_alias(slang)
            except:
                pass

            if not source_language:
                return rc.BAD_REQUEST

            try:
                Resource.objects.get_or_create(project=project,
                    source_language=source_language, **data)
            except:
                return rc.BAD_REQUEST

            return rc.CREATED
        else:
            return rc.BAD_REQUEST

    @method_decorator(one_perm_required_or_403(pr_resource_add_change,
        (Project, 'slug__exact', 'project_slug')))
    def update(self, request, project_slug, resource_slug):
        """
        API call to update resource details via PUT.
        """
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND

        if 'application/json' in request.content_type: # we got JSON
            data = getattr(request, 'data', None)
            slang = data.pop('source_language', None)
            source_language = None
            try:
                source_language = Language.objects.by_code_or_alias(slang)
            except:
                pass

            if resource_slug:
                try:
                    resource = Resource.objects.get(slug=resource_slug)
                except Resource.DoesNotExist:
                    return rc.BAD_REQUEST
                try:
                    for key,value in data.items():
                        setattr(resource, key,value)
                    if source_language:
                        resource.source_language = source_language
                    resource.save()
                except:
                    return rc.BAD_REQUEST

                return rc.ALL_OK

        return rc.BAD_REQUEST


    @method_decorator(one_perm_required_or_403(pr_resource_delete,
        (Project, 'slug__exact', 'project_slug')))
    def delete(self, request, project_slug, resource_slug):
        """
        API call to delete resources via DELETE.
        """
        if resource_slug:
            try:
                resource = Resource.objects.get(slug=resource_slug)
            except Resource.DoesNotExist:
                return rc.NOT_FOUND

            try:
                resource.delete()
            except:
                return rc.INTERNAL_ERROR

            return rc.DELETED
        else:
            return rc.BAD_REQUEST

############################
# Resource String Handlers #
############################

def _create_stringset(request, project_slug, resource_slug, target_lang_code):
    '''
    Helper function to create json stringset for a project/resource for one or
    multiple languages.
    '''
    try:
        if resource_slug:
            resources = [Resource.objects.get(project__slug=project_slug,slug=resource_slug)]
        elif "resources" in request.GET:
            resources = []
            for resource_slug in request.GET["resources"].split(","):
                resources.append(Resource.objects.get(slug=resource_slug))
        else:
            resources = Resource.objects.filter(project__slug=project_slug)
    except Resource.DoesNotExist:
        return rc.NOT_FOUND

    # Getting language codes from the request
    lang_codes = []
    if target_lang_code:
        lang_codes.append(target_lang_code)
    elif "languages" in request.GET:
        lang_codes.extend([l for l in request.GET["languages"].split(",")])

    # Finding the respective Language objects in the database
    target_langs = []
    for lang_code in lang_codes:
        try:
            target_langs.append(Language.objects.by_code_or_alias(lang_code))
        except Language.DoesNotExist:
            logger.info("No language found for code '%s'." % lang_code)

    # If any language is found
    if not target_langs and lang_codes:
        return rc.NOT_FOUND

    # handle string search
    #
    # FIXME: currently it supports case insensitive search. Maybe it should
    # look for exact matches only? Also, there are issues in case insensitive
    # searches in sqlite and UTF8 charsets according to this
    # http://docs.findjango.com/ref/databases.html#sqlite-string-matching
    qstrings = {}
    # user requested specific strings?
    if "strings" in request.GET:
        qstrings = {
            'string__iregex': eval('r\'('+'|'.join(request.GET['strings'].split(',')) + ')\'')
        }

    retval = []
    for translation_resource in resources:
        strings = {}
        for ss in SourceEntity.objects.filter(resource=translation_resource,**qstrings):
            if not ss.id in strings:
                strings[ss.id] = {
            'id':ss.id,
            'original_string':ss.string,
            'context':ss.context,
            'translations':{}}

        if not qstrings:
            translated_strings = Translation.objects.filter(source_entity__resource=translation_resource)
        else:
            translated_strings = Translation.objects.filter(
                                            source_entity__resource = translation_resource,
                                            source_entity__string__iregex=qstrings['string__iregex'])

        if target_langs:
            translated_strings = translated_strings.filter(language__in = target_langs)
        for ts in translated_strings.select_related('source_entity','language'):
            strings[ts.source_entity.id]['translations'][ts.language.code] = ts.string

        retval.append({'resource':translation_resource.slug,'strings':strings.values()})
    return retval


class StatsHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, project_slug, resource_slug, lang_code=None):
        """
        This is an API handler to display translation statistics for individual
        resources.
        """
        try:
            resource = Resource.objects.get( project__slug = project_slug,
                slug= resource_slug)
        except Resource.DoesNotExist:
            return BAD_REQUEST("Unkown resource %s" % resource_slug)

        language = None
        if lang_code:
            try:
                language = Language.objects.by_code_or_alias(lang_code)
            except Language.DoesNotExist:
                return BAD_REQUEST("Unknown language %s" % lang_code)


        stats = ResourceStatsList(resource)
        # TODO: If we're gonna use this as a generic stats generator, we should
        # include more info in the json.
        if language:
            retval = {}
            for stat in stats.resource_stats_for_language(language): 
                retval.update({stat.language.code:{"completed": "%s%%" % stat.trans_percent,
                    "translated_entities": stat.num_translated}})
        else:
            retval = []
            for stat in stats.language_stats():
                retval.append({stat.language.code:{"completed": "%s%%" % stat.trans_percent,
                    "translated_entities": stat.num_translated}})
        return retval

class FileHandler(BaseHandler):
    allowed_methods = ('GET')

    @throttle(100, 60*60)
    @method_decorator(one_perm_required_or_403(pr_project_private_perm,
        (Project, 'slug__exact', 'project_slug')))
    def read(self, request, project_slug, resource_slug=None, language_code=None):
        """
        API Handler to export translation files from the database
        """
        try:
            resource = Resource.objects.get( project__slug = project_slug, slug = resource_slug)
            language = Language.objects.get( code=language_code)
        except (Resource.DoesNotExist, Language.DoesNotExist), e:
            return BAD_REQUEST("%s" % e )

        try:
            template = _compile_translation_template(resource, language)
        except Exception, e:
            return BAD_REQUEST("Error compiling the translation file: %s" %e )

        i18n_method = settings.I18N_METHODS[resource.i18n_type]
        response = HttpResponse(template, mimetype=i18n_method['mimetype'])
        response['Content-Disposition'] = ('attachment; filename="%s_%s%s"' % (
        smart_unicode(resource.name), language.code,
        i18n_method['file-extensions'].split(', ')[0]))

        return response
