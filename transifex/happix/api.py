# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from projects.permissions import *
from txcommon.decorators import one_perm_required_or_403
from happix.models import TResource, SourceString, TranslationString, StorageFile
from languages.models import Language
from projects.models import Project
from txcommon.log import logger
from django.db import transaction
from uuid import uuid4
from happix.decorators import method_decorator


class TResourceHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    model = TResource

    def read(self, request, project_slug, tresource_slug):
        return TResource.objects.filter(project__slug = project_slug)


    #@transaction.commit_manually
    def create(self, request, project_slug, tresource_slug):
        """
        API call for uploading translation files (OBSOLETE since uploading files works via StorageFile now)

        Data required:

        Uploaded file which will be merged with translation resource specified by URL
        
        """
        project = Project.objects.get(slug = project_slug)
            
        translation_resource, created = TResource.objects.get_or_create(
            slug = tresource_slug,
            project = project,
            defaults = {
                'project' : project,
                'name' : tresource_slug.replace("-", " ").replace("_", " ").capitalize()
            })

        for filename, upload in request.FILES.iteritems():
            translation_resource.objects.merge_stream(filename, upload, request.POST['target_language'])
        return rc.CREATED

class StringHandler(BaseHandler):
    allowed_methods = ('GET', 'POST','PUT')

    def read(self, request, project_slug, tresource_slug=None, target_lang_code=None):
        '''
        This api call returns all strings for a specific tresource of a project
        and for a given target language. The data is returned in json format,
        following this organization:

        {
            'tresource': 'sampleresource',
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
        try:
            if tresource_slug:
                resources = [TResource.objects.get(project__slug=project_slug,slug=tresource_slug)]
            elif "resources" in request.GET:
                resources = []
                for resource_slug in request.GET["resources"].split(","):
                    resources.append(TResource.objects.get(slug=resource_slug))
            else:
                resources = TResource.objects.filter(project__slug=project_slug)
        except TResource.DoesNotExist:
            return rc.NOT_FOUND

        try:
            if target_lang_code:
                target_langs = [Language.objects.by_code_or_alias(target_lang_code)]
            elif "languages" in request.GET:
                target_langs = []
                for lang_code in request.GET["languages"].split(","):
                    target_langs.append(Language.objects.by_code_or_alias(lang_code))
            else:
                target_langs = None
        except Language.DoesNotExist:
            return rc.NOT_FOUND

        retval = []
        for translation_resource in resources:
            strings = {}
            for ss in SourceString.objects.filter(tresource = translation_resource):
                if not ss.id in strings:
                    strings[ss.id] = {
		        'id':ss.id,
		        'original_string':ss.string,
		        'context':ss.description,
		        'translations':{}}

            translated_strings = TranslationString.objects.filter(tresource = translation_resource)
            if target_langs:
                translated_strings = translated_strings.filter(language__in = target_langs)
            for ts in translated_strings.select_related('source_string','language'):
                strings[ts.source_string.id]['translations'][ts.language.code] = ts.string

            retval.append({'resource':translation_resource.slug,'strings':strings.values()})
        return retval

    # FIXME: Find out what permissions are needed for this. Maybe implement new
    # ones for TResource similar to Components? Something like 'tresource_edit'
    #@method_decorator(one_perm_required_or_403())
    def create(self, request, project_slug, tresource_slug):
        '''
        This API call is for uploading TranslationStrings to a specific
        TResource. If no corresponding SourceStrings are found, the uploading
        should fail. The translation strings should be created if not in db or
        if already there, they should be overwritten. Format for incoming json
        files is:

        {
          'tresource': 'sampleresource',
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
            translation_resource = TResource.objects.get(slug=tresource_slug)
        except TResource.DoesNotExist:
            return rc.NOT_FOUND

        if 'application/json' in request.content_type: # we got JSON strings
            import json
            try:
                data = json.loads(getattr(request, 'data', None))
            except ValueError, TypeError:
                return rc.BAD_REQUEST

            if not data:
                return rc.BAD_REQUEST

            strings = data.get('strings', [])

            try:
                lang = Language.objects.by_code_or_alias(data.get('language',None))
            except Language.DoesNotExist:
                return rc.BAD_REQUEST

            for s in strings:
                try:
                    ss = SourceString.objects.get(string=s.get('string',None),
                                             description=s.get('context',None),
                                             tresource=translation_resource)
                except SourceString.DoesNotExist:
                    # We have no such string for translation. Either we got
                    # wrong file or something is messed up. Fail...
                    return rc.BAD_REQUEST

                ts, created = TranslationString.objects.get_or_create(
                                    language=lang,
                                    source_string=ss,
                                    tresource=translation_resource)
                ts.string = s.get('value')
                ts.save()

            return rc.CREATED
        else:
            return rc.BAD_REQUEST

    # this probably needs some more fine grained permissions for real world
    # usage. for now all people who can change a project can add/edit resources
    # and strings in it
    @method_decorator(one_perm_required_or_403(pr_project_add_change,
        (Project, 'slug__exact', 'project_slug')))
    def update(self, request, project_slug, tresource_slug, target_lang_code=None):
        '''
        Using this API call, a user may create a tresource and assign source
        strings for a specific language. It gets the project and tresource name
        from the url and the source lang code from the json file. The json
        should be in the following schema:

        {
            'tresource': 'sampleresource',
            'language': 'en',
            'strings':
            [{
                'string': 'str1',
                'value': 'str1.value',
                'occurrence': 'somestring',
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

        # check if tresource exists
        translation_resource, created = TResource.objects.get_or_create(
                                        slug = tresource_slug,
                                        project = translation_project)
        # if new make sure, it's initialized correctly
        if created:
            translation_resource.name = tresource_slug
            translation_resource.project = translation_project
            translation_resource.save()

        if 'application/json' in request.content_type: # we got JSON strings
            import json
            try:
                data = json.loads(getattr(request, 'data', None))
            except ValueError, TypeError:
                return rc.BAD_REQUEST

            if not data:
                return rc.BAD_REQUEST

            strings = data.get('strings', [])
            try:
                lang = Language.objects.by_code_or_alias(data.get('language', 'en'))
            except Language.DoesNotExist:
                return rc.BAD_REQUEST

            # create source strings and translation strings for the source lang
            for s in strings:
                obj, cr = SourceString.objects.get_or_create(string=s.get('string'),
                                    description=s.get('context'),
                                    occurrences=s.get('occurrence'),
                                    tresource=translation_resource)
                ts, created = TranslationString.objects.get_or_create(
                                    language=lang,
                                    source_string=obj,
                                    tresource=translation_resource)
                ts.string = s.get('value')
                ts.save()

            return rc.CREATED
        else:
            return rc.BAD_REQUEST

