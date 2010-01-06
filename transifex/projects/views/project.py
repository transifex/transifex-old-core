# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.dispatch import Signal
from django.utils.translation import ugettext as _
from django.conf import settings
from django.views.generic import list_detail
from django.contrib.auth.decorators import login_required

from actionlog.models import action_logging, LogEntry
from actionlog.filters import LogEntryFilter
from notification import models as notification
from projects.models import Project
from projects.forms import ProjectAccessSubForm, ProjectForm
from projects.permissions import *
from projects import signals
from repowatch import WatchException

# Temporary
from txcommon import notifications as txnotification

from txcommon.decorators import one_perm_required_or_403
from txcommon.log import logger
from txcommon.views import json_result, json_error

def _project_create_update(request, project_slug=None):
    """
    Handler for creating and updating a project.
    
    This function helps to eliminate duplication of code between those two 
    actions, and also allows to apply different permissions checks in the 
    respectives views.
    """

    if project_slug:
        project = get_object_or_404(Project, slug=project_slug)
    else:
        project = None

    if request.method == 'POST':
        # Access Control tab
        if request.POST.has_key('access_control_form'):
            anyone_subform = ProjectAccessSubForm(request.POST, instance=project)
            if anyone_subform.is_valid():
                anyone_subform.save()
                # TODO: Add an ActionLog and Notification here for this action
                return HttpResponseRedirect(request.POST['next'])

        # Details tab
        else:
            project_form = ProjectForm(request.POST, instance=project, 
                                    prefix='project') 
            if project_form.is_valid(): 
                project = project_form.save(commit=False)
                project_id = project.id
                project.save()
                project_form.save_m2m()

                # TODO: Not sure if here is the best place to put it
                Signal.send(signals.post_proj_save_m2m, sender=Project, 
                            instance=project)

                # ActionLog & Notification
                context = {'project': project}
                if not project_id:
                    nt = 'project_added'
                    action_logging(request.user, [project], nt, context=context)
                else:
                    nt = 'project_changed'
                    action_logging(request.user, [project], nt, context=context)
                    if settings.ENABLE_NOTICES:
                        txnotification.send_observation_notices_for(project, 
                                            signal=nt, extra_context=context)

                return HttpResponseRedirect(reverse('project_detail',
                                            args=[project.slug]),)
    else:
        # Make the current user the maintainer when adding a project
        if project:
            initial_data = {}
        else:
            initial_data = {"maintainers": [request.user.pk]}

        project_form = ProjectForm(instance=project, prefix='project',
                                   initial=initial_data)

    return render_to_response('projects/project_form.html', {
        'project_form': project_form,
        'project': project,
    }, context_instance=RequestContext(request))



# Projects
@login_required
@one_perm_required_or_403(pr_project_add)
def project_create(request):
    return _project_create_update(request)

@login_required
@one_perm_required_or_403(pr_project_add_change, 
    (Project, 'slug__exact', 'project_slug'))
def project_update(request, project_slug):
        return _project_create_update(request, project_slug)

@login_required
@one_perm_required_or_403(pr_project_view_log, 
    (Project, 'slug__exact', 'slug'))
def project_timeline(request, *args, **kwargs):
    """
    Present a log of the latest actions on the project.
    
    The view limits the results and uses filters to allow the user to even
    further refine the set.
    """
    project = get_object_or_404(Project, slug=kwargs['slug'])
    log_entries = LogEntry.objects.by_object(project)
    f = LogEntryFilter(request.GET, queryset=log_entries)
    # The template needs both these variables. The first is used in filtering,
    # the second is used for pagination and sorting.
    kwargs.setdefault('extra_context', {}).update({'f': f,
                                                   'actionlog': f.qs})
    return list_detail.object_detail(request, *args, **kwargs)

@login_required
@one_perm_required_or_403(pr_project_delete, 
    (Project, 'slug__exact', 'project_slug'))
def project_delete(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if request.method == 'POST':
        import copy
        project_ = copy.copy(project)
        project.delete()

        request.user.message_set.create(
            message=_("The %s was deleted.") % project.name)

        # ActionLog & Notification
        nt = 'project_deleted'
        context={'project': project_}
        action_logging(request.user, [project_], nt, context=context)

        return HttpResponseRedirect(reverse('project_list'))
    else:
        return render_to_response(
            'projects/project_confirm_delete.html', {'project': project,},
            context_instance=RequestContext(request))


@login_required
def project_toggle_watch(request, project_slug):
    """Add/Remove watches on a project for a specific user."""
    if request.method != 'POST':
        return json_error(_('Must use POST to activate'))

    if not settings.ENABLE_NOTICES:
        return json_error(_('Notification is not enabled'))

    project = get_object_or_404(Project, slug=project_slug)
    url = reverse('project_toggle_watch', args=(project_slug,))

    project_signals = ['project_changed',
                       'project_deleted',
                       'project_component_added',
                       'project_component_changed',
                       'project_component_deleted']
    try:
        result = {
            'style': 'watch_add',
            'title': _('Watch this project'),
            'project': True,
            'url': url,
            'error': None,
        }

        for signal in project_signals:
            notification.stop_observing(project, request.user, signal)

    except notification.ObservedItem.DoesNotExist:
        try:
            result = {
                'style': 'watch_remove',
                'title': _('Stop watching this project'),
                'project': True,
                'url': url,
                'error': None,
            }

            for signal in project_signals:
                notification.observe(project, request.user, signal, signal)

        except WatchException, e:
            return json_error(e.message, result)
    return json_result(result)
