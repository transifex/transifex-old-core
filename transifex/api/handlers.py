# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from happix.models import Resource, SourceString, TranslationString
from languages.models import Language
from projects.models import Project
from storage.models import StorageFile
from txcommon.log import logger
from django.db import transaction
from uuid import uuid4

########################################################
# String Handlers for Projects and Resources          #
########################################################

#def create_json_from_tres_translated_strings(translation_resource, lang_list):
    #'''
    #Given a translation resource and a list of lang codes, this creates the
    #json response with all transtation strings
    #'''

    ## init empty response
    #response = []

    ## iter all languages requested and get all translated strings. append
    ## to the response and then send back
    #for lang in lang_list:
        #try:
            #lang = Language.objects.by_code_or_alias(lang)
        #except Language.DoesNotExist:
            #return rc.BAD_REQUEST

        #strings = TranslationString.objects.filter(
                #resource=translation_resource,
                #language=lang)

        #data_string = []

        #for s in strings:
            #data_string.append({
                #'translated_string':s.string,
                #'occurrence': s.source_string.occurrences,
                #'original_string': s.source_string.string,
            #})

        #response.append({'resource': translation_resource.name,
                       #'target_lang': lang.code,
                       #'strings':  data_string },)

    #return response

#class ProjectStringHandler(BaseHandler):
    #'''
    #Handler to return strings for a whole project or for specific resources
    #inside a project.
    #'''

    #allowed_methods = ('GET',)

    #def read(self, request, project_slug):
        #'''
        #This api calls returns all translation strings for a projects'
        #resources. If no resources are specified, all resource translation
        #strings are returned.

        #To specify specific resources, you can pass the variable with the
        #'resources' variable a comma  separated list of resource slugs and
        #the API will return all translation strings for this resource in all
        #languages available.

        #If you want to request translation of specific languages, you can pass
        #in the 'lang_codes' variable a comma separated list of language codes
        #and only the translations in these languages will be included in the
        #response. If no translation strings are found for a requested language,
        #the API returns an empty list.

        #The response is in the following format:

        #[{
           #"resource": "tres1",
           #"target_lang": "lang1",
           #"strings" :
            #[{
              #"original_string": "str1",
              #"translated_string": "str2",
              #"occurence": "file:lineno",
            #},
            #{
              #...
            #}]
         #},
         #{
           #"resource": "tres1",
           #"target_lang": "lang2",
           #"strings" :
            #[{
              #"original_string": "str1",
              #"translated_string": "str2",
              #"occurence": "file:lineno",
            #},
            #{
              #...
            #}]
         #},
         #{
           #"resource": "tres2",
           #"target_lang": "lang1",
           #"strings" :
            #[{
              #"original_string": "str1",
              #"translated_string": "str2",
              #"occurence": "file:lineno",
            #},
            #{
              #...
            #}]
          #},
            #...
        #]
        #'''
        #response = []

        ## check if user asked for specific languages
        #lang_codes = request.GET.get('lang_codes', None)
        ## check if user asked for specific resources
        #resources = request.GET.get('resources', None)

        #if resources:
            #trs = Resource.objects.filter(slug__in=resources.split(','))
        #else:
            #trs = Resource.objects.filter(project__slug=project_slug) or None

        #if not trs:
            #return rc.BAD_REQUEST

        #for tr in trs:
            #if not lang_codes:
                #language_list = TranslationString.objects.filter(resource=tr).order_by('language').distinct('language').values_list('language__code')
                #language_list = [ l[0] for l in language_list ]
            #else:
                #language_list = lang_codes.split(',')
            #response.append(create_json_from_tres_translated_strings(tr, language_list))

        #return response[0]


#class ResourceStringHandler(BaseHandler):
    #allowed_methods = ('GET', 'POST')

    #def read(self, request, project_slug, resource_slug, target_lang_code=None):
        #'''
        #This api call returns all strings for a specific resource of a project
        #and for a given target language. The data is returned in json format,
        #following this organization:

        #{
            #'resource': 'sampleresource',
            #'target_lang': 'el',
            #'strings':
            #[{
                #'oringinal_string': 'str1',
                #'translated_string': 'str2',
                #'occurrence': 'filename:linenumber'
            #},
            #{
                #...
            #}]
        #}

        #'''

        ## check if we have the requested resource || die
        #try:
             #translation_resource = Resource.objects.get(slug = resource_slug,
                                             #project__slug =project_slug)
        #except Resource.DoesNotExist:
            #return rc.BAD_REQUEST

        ## check if we have the requesed lang || die
        #if target_lang_code:
            #language_list = target_lang_code,
        #else:
            ## check if user asked for specific languages
            #lang_codes = request.GET.get('lang_codes', None)

            ## get all available languages
            #if not lang_codes:
                #language_list = TranslationString.objects.filter(resource=translation_resource).order_by('language').distinct('language').values_list('language__code')
                #language_list = [ l[0] for l in language_list ]
            #else:
                #language_list = lang_codes.split(',')

        #return  create_json_from_tres_translated_strings(translation_resource,
                                                    #language_list)

    #def create(self, request, project_slug, resource_slug):
        #'''
        #Using this API call, a user may create a resource and assign source
        #strings for a specific language. It gets the project and resource name
        #from the url and the source lang code from the json file. The json
        #should be in the following schema:

        #{
            #'resource': 'sampleresource',
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

        ## check if resource exists
        #translation_resource, created = Resource.objects.get_or_create(
                                        #slug = resource_slug,
                                        #project = translation_project)
        ## if new make sure, it's initialized correctly
        #if created:
            #translation_resource.name = resource_slug
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
                                    #description="yadayada",
                                    #resource=translation_resource)
                #ts, created = TranslationString.objects.get_or_create(
                                    #language=lang,
                                    #source_string=obj,
                                    #resource=translation_resource)
                #if created:
                    #ts.string = s.get('value')
                    #ts.save()
        #else:
            #return rc.BAD_REQUEST


"""
This used to be API call for adding translation strings from JSON stringset

        source_language = Language.objects.by_code_or_alias('en')
        j = 0
        if request.content_type:
            translation_resource = Resource.objects.get(id = resource_id)
            try:
#                target_language = Language.objects.by_code_or_alias()
                target_language = Language.objects.by_code_or_alias(request.data['target_language'])
            except Language.DoesNotExist:
                return rc.NOT_IMPLEMENTED
            for i in request.data['strings']:
                ss, created = SourceString.objects.get_or_create(
                    string= i['source_string'],
                    description=i['context'] or "None",
                    resource=translation_resource,
                    defaults = {
                        'position' : 1,
                    }
                )

                sset, created = StringSet.objects.get_or_create(
                    resource=translation_resource,
                    path = request.data['filename'],
                    language = target_language,
                )

                ts, created = TranslationString.objects.get_or_create(
                    source_string=ss,
                    stringset = sset,
                    defaults={
                        'string' : i["translation_string"],
                        'user' : User.objects.get(id=1),
                    },
                )
            j += 1
        transaction.commit()
"""
