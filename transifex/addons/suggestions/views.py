# -*- coding: utf-8 -*-
from django.http import (HttpResponse, HttpResponseBadRequest)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from models import Suggestion
from happix.models import (Translation, SourceEntity)
from languages.models import Language
from projects.models import Project
from projects.permissions import *
from projects.permissions.project import ProjectPermission
from txcommon.decorators import one_perm_required_or_403


# XXX: Rethink about it!!!
# Restrict access only for private projects since this is used to fetch stuff!
# Allow even anonymous access on public projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def get_suggestions(request, project_slug=None, resource_slug=None,
     lang_code=None):
    """
    Ajax view that returns a template snippet for translation suggestions.
    """

    if not request.POST and request.POST.has_key('source_id'):
        return HttpResponseBadRequest()

    source_entity = get_object_or_404(SourceEntity, pk=request.POST['source_id'])

    try:
        current_translation = Translation.objects.get(source_entity=source_entity,
            rule=5, language__code=lang_code)
    except Translation.DoesNotExist:
        current_translation = None

    suggestions = Suggestion.objects.filter(source_entity=source_entity,
        language__code=lang_code).order_by('-score')

    return render_to_response("lotte_suggestions.html",
    { 'suggestions': suggestions,
      'source_entity': source_entity,
      'project_slug': project_slug,
      'resource_slug': resource_slug,
      'lang_code': lang_code,
      'current_translation': current_translation},
    context_instance = RequestContext(request))


# XXX: Rethink about it!!!
# Restrict access only for private projects since this is used to fetch stuff!
# Allow even anonymous access on public projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def suggestion_create(request, project_slug=None, resource_slug=None,
     lang_code=None):
    """
    Ajax view that returns a template snippet for translation suggestions.
    """

    if (not request.POST or not request.POST.has_key('source_id') 
        or not request.POST.has_key('suggestion_string')
        or request.POST['suggestion_string']==''):
        return HttpResponseBadRequest()

    source_entity = get_object_or_404(SourceEntity, pk=request.POST['source_id'])

    language = Language.objects.by_code_or_alias(lang_code)

    # Get or create the new suggestion for the specific user.
    Suggestion.objects.create(
        source_entity=source_entity,
        language=language,
        string=request.POST['suggestion_string'],
        resource=source_entity.resource,
        user=request.user )

    return HttpResponse(status=200)


# TODO: fix perms
def suggestion_vote_updown(request, project_slug=None, resource_slug=None,
     lang_code=None):
    """
    Ajax view for voting on a suggestion.

    This is also used to undo a previously voted suggestion.
    """

    if (not request.POST or not request.POST.has_key('suggestion_id')
        or not request.POST.has_key('vote_type')):
        return HttpResponseBadRequest()

    # Get the suggestion
    suggestion = get_object_or_404(Suggestion, pk=request.POST['suggestion_id'])
    if request.POST['vote_type']=='up':
        suggestion.vote_up(request.user)
    else:
        suggestion.vote_down(request.user)

    return HttpResponse(status=200)
