# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from notification import models as notification
from txcommon.decorators import one_perm_required_or_403
from txcommon.views import (json_result, json_error, permission_denied)
from projects.models import Project, Component
from projects.permissions import pr_project_private_perm
from projects.permissions.project import ProjectPermission
from translations.models import POFile
from errors import WatchException
from models import Watch

@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'))
def component_toggle_watch(request, project_slug, component_slug, filename):
    """Add/Remove a watch for a path on a component for a specific user."""

    if request.method != 'POST':
        return json_error(_('Must use POST to activate'))

    if not settings.ENABLE_NOTICES:
        return json_error(_('Notification is not enabled'))

    component = get_object_or_404(Component, slug=component_slug,
                                project__slug=project_slug)
    ctype = ContentType.objects.get_for_model(Component)

    pofile = get_object_or_404(POFile, object_id=component.pk, 
                               content_type=ctype, filename=filename)

    # FIXME: It's kinda redundancy, only a decorator should be enough
    # Also it's only accepting granular permissions
    check = ProjectPermission(request.user)
    if not check.submit_file(pofile) and not \
        request.user.has_perm('repowatch.add_watch') and not \
        request.user.has_perm('repowatch.delete_watch'):
        return permission_denied(request)

    url = reverse('component_toggle_watch', args=(project_slug, component_slug, 
                                                  filename))
    try:
        watch = Watch.objects.get(path=filename, component=component, 
                                  user__id__exact=request.user.id)
        watch.user.remove(request.user)
        result = {
            'style': 'watch_add',
            'title': _('Watch it'),
            'id': pofile.id,
            'url': url,
            'error': None,
        }
        notification.stop_observing(pofile, request.user, 
                            signal='project_component_file_changed')
    except Watch.DoesNotExist:
        try:
            Watch.objects.add_watch(request.user, component, filename)
            result = {
                'style': 'watch_remove',
                'title': _('Stop watching'),
                'id': pofile.id,
                'url': url,
                'error': None,
            }
            notification.observe(pofile, request.user,
                                 'project_component_file_changed',
                                 signal='project_component_file_changed')
        except WatchException, e:
            return json_error(e.message, result)
    return json_result(result)


@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=False)
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
