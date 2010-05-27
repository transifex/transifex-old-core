# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from happix.models import TResource, SourceString, TranslationString, StorageFile
from languages.models import Language
from projects.models import Project
from txcommon.log import logger
from django.db import transaction
from uuid import uuid4


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
    allowed_methods = ('GET', 'POST')

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
                    strings[ss.id] = {'id':ss.id,'original_string':ss.string,'occurrence':'blah','translations':{}}

            translated_strings = TranslationString.objects.filter(tresource = translation_resource)
            if target_langs:
                translated_strings = translated_strings.filter(language__in = target_langs)
            for ts in translated_strings.select_related('source_string','language'):
                strings[ts.source_string.id]['translations'][ts.language.code] = ts.string
                    
            retval.append({'resource':translation_resource.slug,'strings':strings.values()})
        return retval
        
    def create(self, request, project_slug, tresource_slug, target_lang_code=None):
        """
        API call for inserting list of strings back to database
        Used by Lotte 'Save' and 'Save all' buttons

        Lotte pushes dictionary of translated strings identified by translation string id
        {
            'update' : {
                str(SourceString.id) : str(TranslationString.string)
            }, 
        }

        Return value is dictionary with list of saved objects
        {
            'updated' : [SourceString.id, SourceString.id, ...]
        }
        """
        try:
            translation_resource = TResource.objects.get(slug = tresource_slug, project__slug = project_slug)
            target_language = Language.objects.by_code_or_alias(target_lang_code)
            if "application/json" in request.content_type: 
                # Updating
                ids = [int(id) for id in request.data['update'].keys()]
                ids_updated = []
                for ts in TranslationString.objects.filter(tresource = translation_resource, language = target_language, source_string__id__in = ids):
                    ts.string = request.data['update'][str(ts.source_string.id)]
                    ts.save()
                    ids_updated.append(ts.source_string.id)

                logger.debug("Updated %s translation of source strings: %s" % (target_language.code, ids_updated))
                ids_added = {}
                return {'updated':ids_updated}
            else:
                return rc.BAD_REQUEST
        except Exception, err:
            print err



    """
    Following call should be POST for TResourceHandler I think (by:lauri)
    """
    #def create(self, request, project_slug, tresource_slug):
        #'''
        #Using this API call, a user may create a tresource and assign source
        #strings for a specific language. It gets the project and tresource name
        #from the url and the source lang code from the json file. The json
        #should be in the following schema:

        #{
            #'tresource': 'sampleresource',
            #'source_lang': 'en',
            #'strings':
            #[{
                #'string': 'str1',
                #'value': 'str1.value',
                #'occurrence': 'filename:lineno',
            #},
            #{
            #}]
        #}

        #'''
        ## check translation project is there. if not fail
        #try:
            #translation_project = Project.objects.get(slug=project_slug)
        #except Project.DoesNotExist:
            #return rc.BAD_REQUEST

        ## check if tresource exists
        #translation_resource, created = TResource.objects.get_or_create(
                                        #slug = tresource_slug,
                                        #project = translation_project)
        ## if new make sure, it's initialized correctly
        #if created:
            #translation_resource.name = tresource_slug
            #translation_resource.project = translation_project
            #translation_resource.save()

        #if request.content_type == 'application/json': # we got JSON strings
            #strings = request.data.get('strings', [])
            #source_lang = request.data.get('source_language', 'en')
            #try:
                #lang = Language.objects.by_code_or_alias(source_lang)
            #except Language.DoesNotExist:
                #return rc.BAD_REQUEST

            ## create source strings and translation strings for the source lang
            #for s in strings:
                #obj, cr = SourceString.objects.get_or_create(string=s.get('value'),
                                    #occurrences=s.get('occurrence'),
                                    #description=s.get('occurrence'),
                                    #tresource=translation_resource)
                #ts, created = TranslationString.objects.get_or_create(
                                    #language=lang,
                                    #source_string=obj,
                                    #tresource=translation_resource)
                #if created:
                    #ts.string = s.get('value')
                    #ts.save()
        #else:
            #return rc.BAD_REQUEST


