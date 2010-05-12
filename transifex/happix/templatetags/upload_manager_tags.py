# -*- coding: utf-8 -*-
from django import template
from languages.models import Language
from projects.models import Project
from happix.models import TResource, TranslationFile, PARSERS

register = template.Library()

@register.inclusion_tag("storage/upload_manager.html")
def upload_manager(target_object):
#    print "Target object:", target_object
    if isinstance(target_object, Project):
        project = target_object
        resource = None
    elif isinstance(target_object, TResource):
        project = target_object.project
        resource = target_object
    else:
        project = None
        resource = None
    return {
          'files' : TranslationFile.objects.all(), #, project = project, user = request.user),
          'project' : target_object,
          'parsers' : PARSERS,
          'languages' : Language.objects.all(),
    }
