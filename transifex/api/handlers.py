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

class StorageHandler(BaseHandler):
    allowed_methods = ('GET', 'POST', 'DELETE')
    model = StorageFile
    fields = ('language',('language',('code',)),'total_strings','name','created','uuid','mime_type','size')

    def delete(self, request, uuid=None):
        """
        Deletes file by storage UUID
        """
        try:
            StorageFile.objects.get(uuid = uuid, user = request.user).delete()
        except StorageFile.DoesNotExist:
            return rc.NOT_FOUND
        logger.debug("Deleted file %s" % uuid)
        return rc.DELETED

    def read(self, request, uuid=None):
        """
        Returns list of StorageFile objects
        [
            {
                "total_strings": 1102,
                "uuid": "71f4964c-817b-4778-b3e0-693375cb1355",
                "language": {
                    "code": "et"
                },
                "created": "2010-05-13 07:22:36",
                "size": 187619,
                "mime_type": "application/x-gettext",
                "name": "kmess.master.et.po"
            },
            ...
        ]
        """
        retval = StorageFile.objects.filter(user = request.user, bound=False)
        logger.debug("Returned list of users uploaded files: %s" % retval)
        return retval

    def create(self, request, uuid=None):
        """
        API call for uploading a file via POST or updating storage file attributes
        """
        if "application/json" in request.content_type: # Do API calls
            if request.data.keys() == ['language'] and uuid: # API call for changing language
                lang_code = request.data['language'] # TODO: Sanitize
                try:
                    sf = StorageFile.objects.get(uuid = uuid)
                    if lang_code == "": # Set to 'Not detected'
                        sf.language = None
                    else:
                        sf.language = Language.objects.by_code_or_alias(lang_code)
                except StorageFile.DoesNotExist:
                    return rc.NOT_FOUND # Transation file does not exist
                except Language.DoesNotExist:
                    return rc.NOT_FOUND # Translation file not found
                sf.save() # Save the change
                logger.debug("Changed language of file %s (%s) to %s" % (sf.uuid, sf.name, lang_code))
                return rc.ALL_OK
            return rc.BAD_REQUEST # Unknown API call
        elif "multipart/form-data" in request.content_type: # Do file upload
            if 'userfile' in request.FILES:
                submitted_file = request.FILES['userfile']
                sf = StorageFile()
                sf.name = str(submitted_file.name)
                sf.uuid = str(uuid4())
                file_size = 0
                fh = open(sf.get_storage_path(), 'wb')
                for chunk in submitted_file.chunks():
                    fh.write(chunk)
                    file_size += len(chunk)
                fh.close()
                sf.size = file_size
                sf.user = request.user
                sf.update_props()
                sf.save()
                logger.debug("Uploaded file %s (%s)" % (sf.uuid, sf.name))
                return rc.CREATED
            return rc.FAILED
        else: # Unknown content type/API call
            return rc.BAD_REQUEST

class LanguageHandler(BaseHandler):
    """
    API call for retrieving languages available on Tx

    [
        {
            'code' : 'cd',
            'code_aliases : ' cd-al1 cd-al2 ... ',
            'name' : Language name'
        },
        ...
    ]
    """
    allowed_methods = ('GET',)
    model = Language
    fields = ('code', 'code_aliases', 'name')
    def read(self, request):
        logger.debug("Returned list of all languages")
        return Language.objects.all()

class ProjectHandler(BaseHandler):
    """
    API handler for model Project.
    """
    allowed_methods = ('GET','PUT')
    model = Project
    #TODO: Choose the fields we want to return
    exclude = ()

    def update(self, request, project_slug):
        """
        Creates subelement for project, currently supports creating translation resource by UUID of StorageFile
        """
        if "application/json" in request.content_type:
            if "uuid" in request.data:
                uuid = request.data['uuid']
                project = Project.objects.get(slug=project_slug)
                storage_file = StorageFile.objects.get(uuid=uuid,user=request.user)

                translation_resource, created = TResource.objects.get_or_create(
                        slug = "resource-%s" % (slugify(storage_file.name)),
                        name = "Translations of '%s'" % storage_file.name,
                        project = project,
                )

                logger.debug("Going to insert strings from %s (%s) to %s/%s" % (storage_file.name, storage_file.uuid, project.slug, translation_resource.slug))
                try:
                    strings_added, strings_updated = translation_resource.merge_translation_file(storage_file)
                except Language.DoesNotExist:
                    request.user.message_set.create(
                        message="We could not guess the language of uploaded file")
                else:
                    messages = []
                    if strings_added > 0:
                        messages.append("%i strings added" % strings_added)
                    if strings_updated > 0:
                        messages.append("%i strings updated" % strings_updated)
                    request.user.message_set.create(
                        message=",".join(messages))
                retval= {
                    'added':strings_added,
                    'updated':strings_updated,
                    #'redirect':reverse('project.resource',args=[project.slug, translation_resource.slug])
                    'redirect':reverse('translation',args=[project.slug, translation_resource.slug, storage_file.language.code])
                }
                logger.debug("Extraction successful, returning: %s" % retval)

                # Set StorageFile to 'bound' status, which means that it is bound to some translation resource
                # This also means it will not be shown in 'Uploaded files' box anymore
                storage_file.bound = True
                storage_file.save()
                return retval
            else:
                return rc.BAD_REQUEST
        else:
            return rc.BAD_REQUEST

class StringHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    fields = ('string', ('source_string', ('string',)))
    model = TranslationString
    def read(self, request, project_slug, tresource_slug, target_lang_code=None, source_lang_code=None):
        """
        API call for retrieveing translation string id, source string and translation string tuples

        TODO: Fragmentation, so strings could be loaded in chunks

        This call returns list of strings for project/translation resource

        {
            SourceString.id : {
                'id' : TranslationString(target language).id OR 0,
                'a' : TranslationString(source language).string OR SourceString.string,
                'b' : TranslationString(target language).string OR "",
            },
            ...
        }
        """
        translation_resource = TResource.objects.get(slug = tresource_slug, project__slug = project_slug)
        project = translation_resource.project

        """
        target_language is the language the user is translating INTO
        """
        target_language = Language.objects.by_code_or_alias(target_lang_code)

        """
        source_language is the language FROM what the user is translating,
          if some strings are unavailable, source string is shown instead
        """
        try:
            if not source_lang_code:
                raise Language.DoesNotExist
            source_language = Language.objects.by_code_or_alias(source_lang_code)
        except Language.DoesNotExist: # Fall back to English
            source_language = Language.objects.by_code_or_alias('en')


        logger.debug("Retrieving strings of %s/%s (%s->%s)" % (project, translation_resource, source_language.code, target_language.code))

        d = {}
        for ss in SourceString.objects.filter(tresource = translation_resource):
            if not ss.id in d:
                d[ss.id] = {'a':ss.string,'b':'','id':ss.id}

        for ts in TranslationString.objects.filter(tresource = translation_resource, language = source_language).select_related('source_string'):
            d[ts.source_string.id]['a'] = ts.string

        for ts in TranslationString.objects.filter(tresource = translation_resource, language = target_language).select_related('source_string'):
            d[ts.source_string.id]['b'] = ts.string
        return d

#   This decorator fails with application/json; charset=utf-8 (From Firefox/jQuery.ajax)
#    @require_mime('json')
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

########################################################
# String Handlers for Projects and TResources          #
########################################################

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
            trs = TResource.objects.filter(slug__in=tresources.split(','))
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

        return response[0]


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
                                    description="yadayada",
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


"""
This used to be API call for adding translation strings from JSON stringset

        source_language = Language.objects.by_code_or_alias('en')
        j = 0
        if request.content_type:
            translation_resource = TResource.objects.get(id = tresource_id)
            try:
#                target_language = Language.objects.by_code_or_alias()
                target_language = Language.objects.by_code_or_alias(request.data['target_language'])
            except Language.DoesNotExist:
                return rc.NOT_IMPLEMENTED
            for i in request.data['strings']:
                ss, created = SourceString.objects.get_or_create(
                    string= i['source_string'],
                    description=i['context'] or "None",
                    tresource=translation_resource,
                    defaults = {
                        'position' : 1,
                    }
                )

                sset, created = StringSet.objects.get_or_create(
                    tresource=translation_resource,
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
