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

#
#class StringHandler(BaseHandler):
#    allowed_methods = ('GET', 'POST')
#    fields = ('string', ('source_string', ('string',)))
#    model = TranslationString
#    def read(self, request, project_slug, tresource_slug, target_lang_code=None, source_lang_code=None):
#        """
#        API call for retrieveing translation string id, source string and translation string tuples
#
#        TODO: Fragmentation, so strings could be loaded in chunks
#
#        This call returns list of strings for project/translation resource
#
#        {
#            SourceString.id : {
#                'id' : TranslationString(target language).id OR 0,
#                'a' : TranslationString(source language).string OR SourceString.string,
#                'b' : TranslationString(target language).string OR "",
#            },
#            ...
#        }
#        """
#        translation_resource = TResource.objects.get(slug = tresource_slug, project__slug = project_slug)
#        project = translation_resource.project
#
#        """
#        target_language is the language the user is translating INTO
#        """
#        target_language = Language.objects.by_code_or_alias(target_lang_code)
#
#        """
#        source_language is the language FROM what the user is translating,
#          if some strings are unavailable, source string is shown instead
#        """
#        try:
#            if not source_lang_code:
#                raise Language.DoesNotExist
#            source_language = Language.objects.by_code_or_alias(source_lang_code)
#        except Language.DoesNotExist: # Fall back to English
#            source_language = Language.objects.by_code_or_alias('en')
#
#
#        logger.debug("Retrieving strings of %s/%s (%s->%s)" % (project, translation_resource, source_language.code, target_language.code))
#
#        d = {}
#        for ss in SourceString.objects.filter(tresource = translation_resource):
#            if not ss.id in d:
#                d[ss.id] = {'a':ss.string,'b':'','id':ss.id}
#
#        for ts in TranslationString.objects.filter(tresource = translation_resource, language = source_language).select_related('source_string'):
#            d[ts.source_string.id]['a'] = ts.string
#
#        for ts in TranslationString.objects.filter(tresource = translation_resource, language = target_language).select_related('source_string'):
#            d[ts.source_string.id]['b'] = ts.string
#        return d
#
##   This decorator fails with application/json; charset=utf-8 (From Firefox/jQuery.ajax)
##    @require_mime('json')
#    def create(self, request, project_slug, tresource_slug, target_lang_code=None):
#        """
#        API call for inserting list of strings back to database
#        Used by Lotte 'Save' and 'Save all' buttons
#
#        Lotte pushes dictionary of translated strings identified by translation string id
#        {
#            'update' : {
#                str(SourceString.id) : str(TranslationString.string)
#            }, 
#        }
#
#        Return value is dictionary with list of saved objects
#        {
#            'updated' : [SourceString.id, SourceString.id, ...]
#        }
#        """
#        translation_resource = TResource.objects.get(slug = tresource_slug, project__slug = project_slug)
#        target_language = Language.objects.by_code_or_alias(target_lang_code)
#        if "application/json" in request.content_type: 
#            # Updating
#            ids = [int(id) for id in request.data['update'].keys()]
#            ids_updated = []
#            for ts in TranslationString.objects.filter(tresource = translation_resource, language = target_language, source_string__id__in = ids):
#                ts.string = request.data['update'][str(ts.source_string.id)]
#                ts.save()
#                ids_updated.append(ts.source_string.id)
#
#            logger.debug("Updated %s translation of source strings: %s" % (target_language.code, ids_updated))
#            ids_added = {}
#            return {'updated':ids_updated}
#        else:
#            return rc.BAD_REQUEST
#
#
def create_json_from_tres_translated_strings(translation_resource, lang_list):
    '''
    Given a translation resource and a list of lang codes, this creates the
    json response with all transtation strings
    '''

    # init empty response
    response = []

    # iter all languages requested and get all translated strings. append
    # to the response and then send back
    for lang in lang_list:
        try:
            lang = Language.objects.by_code_or_alias(lang)
        except Language.DoesNotExist:
            return rc.BAD_REQUEST

        strings = TranslationString.objects.filter(
                tresource=translation_resource,
                language=lang)

        data_string = []

        for s in strings:
            data_string.append({
                'translated_string':s.string,
                'occurrence': s.source_string.occurrences,
                'original_string': s.source_string.string,
            })

        response.append({'tresource': translation_resource.name,
                       'target_lang': lang.code,
                       'strings':  data_string },)

    return response

class ProjectStringHandler(BaseHandler):
    '''
    Handler to return strings for a whole project or for specific tresources
    inside a project.
    '''

    allowed_methods = ('GET',)

    def read(self, request, project_slug):
        '''
        This api calls returns all translation strings for a projects'
        tresources. If no tresources are specified, all tresource translation
        strings are returned.

        To specify specific tresources, you can pass the variable with the
        'tresources' variable a comma  separated list of tresource slugs and
        the API will return all translation strings for this tresource in all
        languages available.

        If you want to request translation of specific languages, you can pass
        in the 'lang_codes' variable a comma separated list of language codes
        and only the translations in these languages will be included in the
        response. If no translation strings are found for a requested language,
        the API returns an empty list.

        The response is in the following format:

        [{
           "tresource": "tres1",
           "target_lang": "lang1",
           "strings" :
            [{
              "original_string": "str1",
              "translated_string": "str2",
              "occurence": "file:lineno",
            },
            {
              ...
            }]
         },
         {
           "tresource": "tres1",
           "target_lang": "lang2",
           "strings" :
            [{
              "original_string": "str1",
              "translated_string": "str2",
              "occurence": "file:lineno",
            },
            {
              ...
            }]
         },
         {
           "tresource": "tres2",
           "target_lang": "lang1",
           "strings" :
            [{
              "original_string": "str1",
              "translated_string": "str2",
              "occurence": "file:lineno",
            },
            {
              ...
            }]
          },
            ...
        ]
        '''
        response = []

        # check if user asked for specific languages
        lang_codes = request.GET.get('lang_codes', None)
        # check if user asked for specific tresources
        tresources = request.GET.get('tresources', None)

        if tresources:
            trs = TResource.objects.filter(slug__in=tresources.split(',')) or None
        else:
            trs = TResource.objects.filter(project__slug=project_slug) or None

        if not trs:
            return rc.BAD_REQUEST

        for tr in trs:
            if not lang_codes:
                language_list = TranslationString.objects.filter(tresource=tr).order_by('language').distinct('language').values_list('language__code')
                language_list = [ l[0] for l in language_list ]
            else:
                language_list = lang_codes.split(',')
            response.append(create_json_from_tres_translated_strings(tr, language_list))

        return response


class TResourceStringHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')

    def read(self, request, project_slug, tresource_slug, target_lang_code=None):
        '''
        This api call returns all strings for a specific tresource of a project
        and for a given target language. The data is returned in json format,
        following this organization:

        {
            'tresource': 'sampleresource',
            'target_lang': 'el',
            'strings':
            [{
                'oringinal_string': 'str1',
                'translated_string': 'str2',
                'occurrence': 'filename:linenumber'
            },
            {
                ...
            }]
        }

        '''

        # check if we have the requested tresource || die
        try:
             translation_resource = TResource.objects.get(slug = tresource_slug,
                                             project__slug =project_slug)
        except TResource.DoesNotExist:
            return rc.BAD_REQUEST

        # check if we have the requesed lang || die
        if target_lang_code:
            language_list = target_lang_code,
        else:
            # check if user asked for specific languages
            lang_codes = request.GET.get('lang_codes', None)

            # get all available languages
            if not lang_codes:
                language_list = TranslationString.objects.filter(tresource=translation_resource).order_by('language').distinct('language').values_list('language__code')
                language_list = [ l[0] for l in language_list ]
            else:
                language_list = lang_codes.split(',')

        return  create_json_from_tres_translated_strings(translation_resource,
                                                    language_list)

    def create(self, request, project_slug, tresource_slug):
        '''
        Using this API call, a user may create a tresource and assign source
        strings for a specific language. It gets the project and tresource name
        from the url and the source lang code from the json file. The json
        should be in the following schema:

        {
            'tresource': 'sampleresource',
            'source_lang': 'en',
            'strings':
            [{
                'string': 'str1',
                'value': 'str1.value',
                'occurrence': 'filename:lineno',
            },
            {
            }]
        }

        '''
        # check translation project is there. if not fail
        try:
            translation_project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.BAD_REQUEST

        # check if tresource exists
        translation_resource, created = TResource.objects.get_or_create(
                                        slug = tresource_slug,
                                        project = translation_project)
        # if new make sure, it's initialized correctly
        if created:
            translation_resource.name = tresource_slug
            translation_resource.project = translation_project
            translation_resource.save()

        if request.content_type == 'application/json': # we got JSON strings
            strings = request.data.get('strings', [])
            source_lang = request.data.get('source_language', 'en')
            try:
                lang = Language.objects.by_code_or_alias(source_lang)
            except Language.DoesNotExist:
                return rc.BAD_REQUEST

            # create source strings and translation strings for the source lang
            for s in strings:
                obj, cr = SourceString.objects.get_or_create(string=s.get('value'),
                                    occurrences=s.get('occurrence'),
                                    description=s.get('occurrence'),
                                    tresource=translation_resource)
                ts, created = TranslationString.objects.get_or_create(
                                    language=lang,
                                    source_string=obj,
                                    tresource=translation_resource)
                if created:
                    ts.string = s.get('value')
                    ts.save()
        else:
            return rc.BAD_REQUEST


