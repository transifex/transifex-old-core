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

from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger
from transifex.projects.permissions import *
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.storage.models import StorageFile

from transifex.resources.decorators import method_decorator
from transifex.resources.models import Resource, SourceEntity, Translation
from transifex.resources.stats import ResourceStatsList
from transifex.resources.views import _compile_translation_template

from transifex.api.utils import BAD_REQUEST

class ResourceHandler(BaseHandler):
    """
    Resource Handler for CRUD operations.
    """

    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')
    model = Resource
    fields = ('slug', 'name', 'created', 'available_languages', 'i18n_type',
        'source_language')
    exclude = ()

    def read(self, request, project_slug, resource_slug=None):
        """
        Get details of a resource.
        """
        if resource_slug:
            try:
                resource = Resource.objects.get(slug=resource_slug,
                    project__slug=project_slug)
                res_stats = ResourceStatsList(resource).resource_stats().next()
                setattr(resource, 'available_languages',
                    res_stats.available_languages_without_teams)
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
                return BAD_REQUEST("No source language was specified.")

            try:
                Resource.objects.get_or_create(project=project,
                    source_language=source_language, **data)
            except:
                return BAD_REQUEST("The json you provided is misformatted.")

            return rc.CREATED
        else:
            return BAD_REQUEST("The request data need to be in json encoding.")

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
                    return BAD_REQUEST("Request %s does not exist" % resource_slug)
                try:
                    for key,value in data.items():
                        setattr(resource, key,value)
                    if source_language:
                        resource.source_language = source_language
                    resource.save()
                except:
                    return rc.BAD_REQUEST

                return rc.ALL_OK

        return BAD_REQUEST("The request data need to be in json encoding.")


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
            return BAD_REQUEST("Unknown resource %s" % resource_slug)

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
                    "translated_entities": stat.num_translated, "last_update":
                    stat.last_update}})
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
            language = Language.objects.by_code_or_alias( code=language_code)
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
