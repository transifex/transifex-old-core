# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import (HttpResponseRedirect, HttpResponse, Http404, 
                         HttpResponseForbidden, HttpResponseBadRequest)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from actionlog.models import action_logging
from happix.models import (Translation, Resource, SourceEntity, PARSERS,
                           StorageFile)
from happix.forms import ResourceForm
from languages.models import Language
from projects.models import Project
from projects.permissions import *
from projects.permissions.project import ProjectPermission
from teams.models import Team
from txcommon.decorators import one_perm_required_or_403

from authority.views import permission_denied

try:
    import json
except:
    import simplejson as json


@login_required
def search_translation(request):
    """
    Return a set of results on translations, given a set of terms as query.
    """
    query_string = request.GET.get('q', "")
    source_lang = request.GET.get('source_lang',None)
    if source_lang == "any_lang":
        source_lang = None
    target_lang = request.GET.get('target_lang',None)
    if target_lang == "choose_lang" or target_lang == "any_lang":
        target_lang = None
    search_terms = query_string.split()

    results = []
    result_count = None

    if search_terms:
        results = Translation.objects.by_string_and_language(
                    string=query_string,
                    source_code=source_lang,
                    target_code=target_lang)
        result_count = len(results)

    return render_to_response("search_translation.html",
                              {'languages': Language.objects.all(),
                               'query': query_string, 
                               'terms': search_terms, 
                               'result_count': result_count,
                               'results': results}, 
                              context_instance = RequestContext(request))


# Restrict access only for private projects 
# Allow even anonymous access on public projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def resource_detail(request, project_slug, resource_slug):
    """
    Return the details overview of a project resource.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                 slug = resource_slug)

    # We want the teams to check in which languages user is permitted to translate.
    user_teams = []
    if getattr(request, 'user'):
        user_teams = Team.objects.filter(project=resource.project).filter(
            Q(coordinators=request.user)|
            Q(members=request.user)).distinct()

    return render_to_response("resource.html",
        { 'project' : resource.project,
          'resource' : resource,
          'languages' : Language.objects.order_by('name'),
          'translated_languages' : resource.available_languages,
          'user_teams' : user_teams },
        context_instance = RequestContext(request))


@one_perm_required_or_403(pr_resource_delete,
                          (Project, "slug__exact", "project_slug"))
def resource_delete(request, project_slug, resource_slug):
    """
    Delete a Translation Resource in a specific project.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                 slug = resource_slug)
    if request.method == 'POST':
        import copy
        resource_ = copy.copy(resource)
        resource.delete()

        request.user.message_set.create(
            message=_("The %s translation resource was deleted.") % resource_.name)

        #TODO: Create the specific notice type and update all the other actions.
        # ActionLog & Notification
#        nt = 'resource_deleted'
#        context={'resource': resource_}
#        action_logging(request.user, [resource_], nt, context=context)

        return HttpResponseRedirect(reverse('project_detail', 
                                    args=[resource.project.slug]),)
    else:
        return render_to_response(
            'resource_confirm_delete.html', {'resource': resource,},
            context_instance=RequestContext(request))



@one_perm_required_or_403(pr_resource_edit,
                          (Project, "slug__exact", "project_slug"))
def resource_edit(request, project_slug, resource_slug):
    """
    Edit the metadata of  a Translation Resource in a specific project.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                  slug = resource_slug)

    if request.method == 'POST':
        resource_form = ResourceForm(request.POST, instance=resource,) 
        if resource_form.is_valid(): 
            resource_new = resource_form.save()

            # TODO: (Optional) Put some signal here to denote the udpate.

            # FIXME: enable the following actionlog
            # ActionLog & Notification
#            context = {'resource': resource}
#            nt = 'resource_changed'
#            action_logging(request.user, [resource], nt, context=context)
#            if settings.ENABLE_NOTICES:
#                txnotification.send_observation_notices_for(resource, 
#                                    signal=nt, extra_context=context)

            return HttpResponseRedirect(reverse('project_detail',
                                        args=[resource.project.slug]),)
    else:
        if resource:
            initial_data = {}

        resource_form = ResourceForm(instance=resource)

    return render_to_response('resource_form.html', {
        'resource_form': resource_form,
        'resource': resource,
    }, context_instance=RequestContext(request))


#XXX: Obsolete
def view_translation(request, project_slug=None, resource_slug=None, lang_code=None):
    translation_resource = Resource.objects.get(
        slug = resource_slug,
        project__slug = project_slug
    )
    target_language = Language.objects.by_code_or_alias(lang_code)
    
    return render_to_response("stringset.html",
        { 'project' : translation_resource.project,
          'resource' : translation_resource,
          'target_language' : target_language,
          'rows' : range(0,10),
          'WEBTRANS_SUGGESTIONS': settings.WEBTRANS_SUGGESTIONS},
        context_instance = RequestContext(request))


#XXX: Obsolete
def start_new_translation(request, project_slug=None, resource_slug=None,
                                    target_lang_code=None):
    '''
    Create new language for specified resource.
    '''

    resource = Resource.objects.get(
        slug = resource_slug,
        project__slug = project_slug
    )

    strings = SourceEntity.objects.filter(resource=resource)

    target_lang = Language.objects.get(code=target_lang_code)

    for s in strings:
        Translation.objects.get_or_create(
                    resource = resource,
                    language = target_lang,
                    source_string = s.source_string)


# Restrict access only for private projects 
# Allow even anonymous access on public projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def resource_actions(request, project_slug=None, resource_slug=None,
                     target_lang_code=None):
    """
    Ajax view that returns an fancybox template snippet for resource specific 
    actions.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                 slug = resource_slug)
    target_language = get_object_or_404(Language, code=target_lang_code)
    project = resource.project
    # Get the team if exists to use it for permissions and links
    team = Team.objects.get_or_none(project, target_lang_code)

    return render_to_response("resource_actions.html",
    { 'project' : project,
      'resource' : resource,
      'target_language' : target_language,
      'team' : team},
    context_instance = RequestContext(request))


# Restrict access only for private projects 
# Allow even anonymous access on public projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def project_resources(request, project_slug=None, offset=None, **kwargs):
    """
    Ajax view that returns a table snippet for all the resources in a project.
    
    If offset is provided, then the returned table snippet includes only the
    rows beginning from the offset and on.
    """
    more = kwargs.get('more', False)
    MORE_ENTRIES = 5
    project = get_object_or_404(Project, slug=project_slug)
    total = Resource.objects.filter(project=project).count()
    begin = int(offset)
    end_index = (begin + MORE_ENTRIES)
    resources = Resource.objects.filter(project=project)[begin:]
    # Get the slice :)
    if more and (not end_index >= total):
        resources = resources[begin:end_index]

    return render_to_response("resource_list_more.html",
    { 'project' : project,
      'resources' : resources,},
    context_instance = RequestContext(request))


#FIXME: Permissions
def clone_language(request, project_slug=None, resource_slug=None,
            source_lang_code=None, target_lang_code=None):
    '''
    Get a resource, a src lang and a target lang and clone all translation
    strings for the src to the target.

    The user is redirected to the online editor for the target language.
    '''

    resource = Resource.objects.get(
        slug = resource_slug,
        project__slug = project_slug
    )
    # get the strings which will be cloned
    strings = Translation.objects.filter(
                resource = resource,
                language__code = source_lang_code)

    target_lang = Language.objects.get(code=target_lang_code)

    # clone them in new translation
    for s in strings:
        Translation.objects.get_or_create(
                    resource = resource,
                    language = target_lang,
                    string = s.string,
                    source_entity = s.source_entity,
                    number = s.number)
    return HttpResponseRedirect(reverse('translate', args=[project_slug,
                                resource_slug, target_lang_code]),)


# Restrict access only to maintainers of the projects.
@one_perm_required_or_403(pr_resource_translations_delete,
                          (Project, "slug__exact", "project_slug"))
def resource_translations_delete(request, project_slug, resource_slug, lang_code):
    """
    Delete the set of Translation objects for a specific Language in a Resource.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                 slug = resource_slug)

    language = get_object_or_404(Language, code=lang_code)

    # Use a flag to denote if there is an attempt to delete the source language.
    is_source_language = False
    if resource.source_language == language:
        is_source_language = True

    if request.method == 'POST':
        Translation.objects.filter(resource=resource, language=language).delete()

        request.user.message_set.create(
            message=_("The translations of %s language for the %s resource were "
                      "deleted successfully.") % (language.name, resource.name))

        #TODO: Create the specific notice type and update all the other actions.

        return HttpResponseRedirect(reverse('resource_detail',
                                    args=[resource.project.slug, resource.slug]),)
    else:
        return render_to_response(
            'resource_translations_confirm_delete.html',
            {'resource': resource,
             'language': language,
             'is_source_language': is_source_language},
            context_instance=RequestContext(request))


def not_available(request, project_slug, lang_code, resource_slug = None):
    """
    View to inform the user when the lotte addon is not available that
    online translations are not supported.
    """

    return render_to_response("not_available.html",
                              context_instance = RequestContext(request))
