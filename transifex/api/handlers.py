# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc
from django.contrib.auth.models import User
from happix.models import TResource, SourceString, TranslationString, TranslationFile
from languages.models import Language
from projects.models import Project

from django.db import transaction
import uuid

class StorageHandler(BaseHandler):
    allowed_methods = ('GET', 'POST', 'DELETE')
    model = TranslationFile
    fields = ('source_language',('source_language',('code',)),'total_strings','name','created','storage_uuid','mime_type','size')
    def delete(self, request, storage_uuid=None):
        """
        TODO: Check permissions
        """
        try:
            TranslationFile.objects.get(storage_uuid = storage_uuid).delete()
        except TranslationFile.DoesNotExist:
            return rc.NOT_FOUND
        return rc.DELETED

    def read(self, request, storage_uuid=None):
        print "reading.."
        return TranslationFile.objects.all()

    def create(self, request, storage_uuid=None):
        """
        API call for uploading a file via POST or updating storage file attributes
        """
        print "content type:",request.content_type
        if "application/json" in request.content_type: # Do API calls
            print "Doing API call..."
            if request.data.keys() == ['language'] and storage_uuid: # API call for changing language
                print "SO FAR SO GOOF"
                lang_code = request.data['language'] # TODO: Sanitize
                try:
                    tf = TranslationFile.objects.get(storage_uuid = storage_uuid)
                    tf.source_language = Language.objects.by_code_or_alias(lang_code) # TODO:Rename source_language for consistency
                except TranslationFile.DoesNotExist:
                    return rc.NOT_FOUND # Transation file does not exist
                except Language.DoesNotExist:
                    return rc.NOT_FOUND # Translation file not found
                tf.save() # Save the change
                return rc.ALL_OK
            return rc.BAD_REQUEST # Unknown API call
        elif "multipart/form-data" in request.content_type: # Do file upload
            print "Uploading file..."
	    if 'userfile' in request.FILES:
		submitted_file = request.FILES['userfile']
		translation_file = TranslationFile()
		translation_file.name = str(submitted_file.name)
		translation_file.storage_uuid = str(uuid.uuid4())
		file_size = 0
		fh = open(translation_file.get_storage_path(), 'wb')
		for chunk in submitted_file.chunks():
		    fh.write(chunk)
		    file_size += len(chunk)
		fh.close()
		translation_file.size = file_size
		translation_file.update_props()
		translation_file.save()
		return rc.CREATED
	    return rc.FAILED
        else: # Unknown content type
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

class ProjectHandler(BaseHandler):
    """
    API handler for model Project.
    """
    allowed_methods = ('GET',)
    model = Project
    #TODO: Choose the fields we want to return
    exclude = ()

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
        if request.content_type: 
            # Updating
            ids = [int(id) for id in request.data['update'].keys()]
            ids_updated = []
            for ts in TranslationString.objects.filter(tresource = translation_resource, language = target_language, source_string__id__in = ids):
                ts.string = request.data['update'][str(ts.source_string.id)]
                ts.save()
                ids_updated.append(ts.source_string.id)

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
        API call for uploading translation files

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