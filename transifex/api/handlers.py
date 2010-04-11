# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc

from happix.models import TResource, SourceString, TranslationString
from languages.models import Language
from projects.models import Project

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
    """
    API handler for the model TResource.
    
    This handler returns the set of strings corresponding to the specific 
    TResource which is referred by its unique id. If a language code is given,
    then the translation strings are returned.
    """
    allowed_methods = ('GET',)
    model = TResource

    def read(self, request, project_id, tresource_id, lang_code=None):
        """Return a list of the source or translation strings"""
        # Get the source strings if no language given.
        results = SourceString.objects.filter(tresource__project__pk=project_id,
                                              tresource__pk=tresource_id,
                                              position__isnull=False)
        # If a specific language has been given return translations.
        if lang_code:
            lang = Language.objects.by_code_or_alias(lang_code)
            results = TranslationString.objects.filter(source_string__in=results,
                                                       language=lang)
        return results
