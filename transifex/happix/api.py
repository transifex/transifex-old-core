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

