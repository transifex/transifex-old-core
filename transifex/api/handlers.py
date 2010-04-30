# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc
from django.contrib.auth.models import User
from happix.models import TResource, SourceString, TranslationString, StringSet
from languages.models import Language
from projects.models import Project

from django.db import transaction

#TODO: Create handlers for stats, for languages supporting by every project.

class ProjectHandler(BaseHandler):
    """
    API handler for model Project.
    """
    allowed_methods = ('GET',)
    model = Project
    #TODO: Choose the fields we want to return
    exclude = ()

class TResourceHandler(BaseHandler):
    @transaction.commit_manually
    def create(self, request, project_id, tresource_id): #, lang_code=None):
        source_language = Language.objects.by_code_or_alias('en')

        j = 0
        if request.content_type:
            translation_resource = TResource.objects.get(id = tresource_id)
            try:
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
