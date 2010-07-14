# -*- coding: utf-8 -*-
from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from projects.permissions import *
from txcommon.decorators import one_perm_required_or_403
from happix.models import Resource, SourceEntity, Translation
from languages.models import Language
from projects.models import Project
from storage.models import StorageFile
from txcommon.log import logger
from django.db import transaction
from uuid import uuid4
from happix.decorators import method_decorator


class ResourceHandler(BaseHandler):
    """
    Resource Handler for CRUD operations.
    """

    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')
    model = Resource
    fields = ('slug', 'name', 'created',)
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
            return Resource.objects.all()

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
            translated_strings = Translation.objects.filter(resource = translation_resource)
        else:
            translated_strings = Translation.objects.filter(
                                            resource = translation_resource,
                                            source_entity__string__iregex=qstrings['string__iregex'])

        if target_langs:
            translated_strings = translated_strings.filter(language__in = target_langs)
        for ts in translated_strings.select_related('source_entity','language'):
            strings[ts.source_entity.id]['translations'][ts.language.code] = ts.string

        retval.append({'resource':translation_resource.slug,'strings':strings.values()})
    return retval


class AnonymousStringHandler(AnonymousBaseHandler):
    allowed_methods = ('GET')

    def read(self, request, project_slug, resource_slug=None, target_lang_code=None):
        '''
        Same as the handler below but this is for anonymous users.
        '''
        return _create_stringset(request, project_slug, resource_slug, target_lang_code)


class StringHandler(BaseHandler):
    allowed_methods = ('GET', 'POST','PUT')
    anonymous = AnonymousStringHandler

    def read(self, request, project_slug, resource_slug=None, target_lang_code=None):
        '''
        This api call returns all strings for a specific resource of a project
        and for a given target language. The data is returned in json format,
        following this organization:

        {
            'resource': 'sampleresource',
            'strings':
            [{
                'oringinal_string': 'str1',
                'translations': {
                  'el': 'str2',
                  'fi' : 'str2'
                }
                'occurrence': 'filename:linenumber'
            },
            {
                ...
            }]
        }

        '''
        return _create_stringset(request, project_slug, resource_slug, target_lang_code)

    # FIXME: Find out what permissions are needed for this. Maybe implement new
    # ones for Resource similar to Components? Something like 'resource_edit'
    #@method_decorator(one_perm_required_or_403())
    def update(self, request, project_slug, resource_slug,target_lang_code=None):
        '''
        This API call is for uploading Translations to a specific
        Resource. If no corresponding SourceEntitys are found, the uploading
        should fail. The translation strings should be created if not in db or
        if already there, they should be overwritten. Format for incoming json
        files is:

        {
          'resource': 'sampleresource',
          'language': 'el',
          'strings' :
            [{
              'string' : 'str1',
              'value' : 'str2',
              'occurrence' : 'somestring',
              'context' : 'someotherstring'
            },
            {
              ....
            }]
        }

        '''
        try:
            translation_project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND

        try:
            translation_resource = Resource.objects.get(slug=resource_slug)
        except Resource.DoesNotExist:
            return rc.NOT_FOUND

        if 'application/json' in request.content_type: # we got JSON strings
            data = getattr(request, 'data',None)

            if not data:
                return rc.BAD_REQUEST

            try:
                strings = data.get('strings', [])
            except AttributeError:
                return rc.BAD_REQUEST

            try:
                lang = Language.objects.by_code_or_alias(data.get('language',None))
            except Language.DoesNotExist:
                try:
                    lang = Language.objects.by_code_or_alias(target_lang_code)
                except Language.DoesNotExist:
                    return rc.BAD_REQUEST

            # Get the committer if exists
            committer = None
            if request and hasattr(request, 'user'):
                committer = getattr(request, 'user', None)

            for s in strings:
                try:
                    ss = SourceEntity.objects.get(string=s.get('string',None),
                                                context=s.get('context',None),
                                                resource=translation_resource)
                except SourceEntity.DoesNotExist:
                    # We have no such string for translation. Either we got
                    # wrong file or something is messed up. Fail...
                    return rc.BAD_REQUEST

                try:
                    ts = Translation.objects.get(language=lang, source_entity=ss,
                                                 resource=translation_resource)
                    # For a existing Translation delete the value if we get a '' or None value
                    if s.get('value'):
                        ts.string = s.get('value')
                        if committer:
                            ts.user = committer
                        ts.save()
                    else:
                        ts.delete()
                except Translation.DoesNotExist:
                    # For new Translations store the value only if it is not None or ''!
                    if s.get('value'):
                        ts = Translation.objects.create(language=lang,
                                source_entity=ss,
                                resource=translation_resource,
                                string=s.get('value'),
                                user=committer)

            return rc.ALL_OK
        else:
            return rc.BAD_REQUEST

    # this probably needs some more fine grained permissions for real world
    # usage. for now all people who can change a project can add/edit resources
    # and strings in it
    #@method_decorator(one_perm_required_or_403(pr_project_add_change,
    #    (Project, 'slug__exact', 'project_slug')))
    def create(self, request, project_slug, resource_slug):
        '''
        Using this API call, a user may create a resource and assign source
        strings for a specific language. It gets the project and resource name
        from the url and the source lang code from the json file. The json
        should be in the following schema:

        {
            'resource': 'sampleresource',
            'language': 'en',
            'strings':
            [{
                'string': 'str1',
                'occurrences': 'somestring',
                'context': 'someotherstring'
            },
            {
            }]
        }

        '''
        # check translation project is there. if not fail
        try:
            translation_project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND

        if 'application/json' in request.content_type: # we got JSON strings
            data = getattr(request, 'data', None)

            if not data:
                return rc.BAD_REQUEST

            # get lang
            try:
                lang = Language.objects.by_code_or_alias(data.get('language', 'en'))
            except Language.DoesNotExist:
                return rc.BAD_REQUEST

            # Get the committer if exists
            committer = None
            if request and hasattr(request, 'user'):
                committer = getattr(request, 'user', None)

            # check if resource exists
            translation_resource, created = Resource.objects.get_or_create(
                                            slug = resource_slug,
                                            source_language = lang,
                                            project = translation_project)
            # if new make sure, it's initialized correctly
            if created:
                translation_resource.name = resource_slug
                translation_resource.project = translation_project
                translation_resource.source_language = lang
                translation_resource.save()

            # get strings
            strings = data.get('strings', [])

            # create source strings and translations for the source lang
            for s in strings:
                # Store the value only if it is not None or ''!
                if s.get('string'):
                    obj, cr = SourceEntity.objects.get_or_create(
                                resource=translation_resource,**s)
                    ts, created = Translation.objects.get_or_create(
                                        language=lang,
                                        source_entity=obj,
                                        resource=translation_resource,
                                        user=committer)
                    ts.string = s.get('string')
                    ts.save()

            return rc.CREATED
        else:
            return rc.BAD_REQUEST

