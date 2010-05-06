# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc
from django.contrib.auth.models import User
from happix.models import TResource, SourceString, TranslationString
from languages.models import Language
from projects.models import Project

from django.db import transaction
from happix.libtransifex.qt import LinguistParser
from happix.libtransifex.java import JavaPropertiesParser

PARSERS = [LinguistParser, JavaPropertiesParser]

class LanguageHandler(BaseHandler):
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
    def read(self, request, project_slug, tresource_slug, lang_code=None):
        """
        API call for retrieveing translation string id, source string and translation string tuples

        TODO: Fragmentation so strings could be loaded in chunks
        """
        translation_resource = TResource.objects.get(slug = tresource_slug, project__slug = project_slug)
        target_language = Language.objects.by_code_or_alias(lang_code)
        retval = []
        for ts in TranslationString.objects.filter(tresource = translation_resource, language = target_language):
            ss = ts.source_string
            retval.append((ts.id, ss.string, ts.string))
        return retval

#   This decorator fails with application/json; charset=utf-8 (From Firefox/jQuery.ajax)
#    @require_mime('json')
    def create(self, request, project_slug, tresource_slug, lang_code=None):
        """
        API call for inserting list of strings back to database
        Used by Lotte 'Save' and 'Save all' buttons

        Lotte pushes dictionary of translated strings identified by translation string id
        {
          str(TranslationString.id) : str(TranslationString.string)
        }

        Return value is dictionary with list of saved objects
        {
          'saved' : [id, id, ...]
        }
        """
        translation_resource = TResource.objects.get(slug = tresource_slug, project__slug = project_slug)
        target_language = Language.objects.by_code_or_alias(lang_code)
        if request.content_type: 
            ids = [int(id) for id in request.data.keys()]
            ids_saved = []
            for ts in TranslationString.objects.filter(tresource = translation_resource, language = target_language, id__in = ids):
                ts.string = request.data[str(ts.id)]
                ts.save()
                ids_saved.append(ts.id)
            return {'saved':ids_saved}
        else:
            return rc.BAD_REQUEST


class TResourceHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    model = TResource

    def read(self, request, project_slug, tresource_slug):
        return TResource.objects.filter(project__slug = project_slug)


    @transaction.commit_manually
    def create(self, request, project_slug, tresource_slug):
        """
        API call for uploading translation files
        """
        def parse_upload(filename, upload):
            for parser in PARSERS:
                if parser.accept(filename):
                    return parser.open(fd = upload)
            return None

        project = Project.objects.get(slug = project_slug)
            
        translation_resource, created = TResource.objects.get_or_create(
            slug = tresource_slug,
            project = project,
            defaults = {
                'project' : project,
                'name' : tresource_slug.replace("-", " ").replace("_", " ").capitalize()
            })

        committer = User.objects.get(id=1)
        for filename, upload in request.FILES.iteritems():
            _stringset = parse_upload(filename, upload)
            target_language = Language.objects.by_code_or_alias(_stringset.target_language or request.POST['target_language'])

            for j in _stringset.strings:
                # If is primary language update source strings!
                ss, created = SourceString.objects.get_or_create(
                    string= j.source_string,
                    description=j.context or "None",
                    tresource=translation_resource,
                    defaults = {
                        'position' : 1,
                    }
                )
                ts, created = TranslationString.objects.get_or_create(
                    source_string=ss,
                    language = target_language,
                    tresource = translation_resource,
                    defaults={
                        'string' : j.translation_string,
                        'user' : committer,
                    },
                )
        transaction.commit()
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