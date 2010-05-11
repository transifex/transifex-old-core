# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from txcommon.decorators import one_perm_required_or_403
from projects.models import Project, Component
from projects.views.component import component_detail
from translations.models import POFile
from teams.models import Team
from models import POFileLock, POFileLockError
from permissions import pr_component_lock_file
from projects.models import Project
import settings

try:
    TFC_CACHING_PREFIX = settings.TFC_CACHING_PREFIX
except:
    TFC_CACHING_PREFIX = ""

@login_required
@one_perm_required_or_403(pr_component_lock_file, 
    (Project, 'slug__exact', 'project_slug'))
def component_file_unlock(request, project_slug, component_slug,
                               filename):
    extra_context = None
    if request.method == 'POST':
        component = get_object_or_404(Component, slug=component_slug,
                                    project__slug=project_slug)
        ctype = ContentType.objects.get_for_model(Component)

        pofile = get_object_or_404(POFile, object_id=component.pk, 
                                   content_type=ctype, filename=filename)
        lock = POFileLock.objects.get_valid(pofile)
        if lock:
            try:
                lock.delete_by_user(request.user)
                cache.delete(TFC_CACHING_PREFIX +'.component.'+component.full_name)
                request.user.message_set.create(message=_("Lock removed."))
            except POFileLockError, err:
                return HttpResponseForbidden("You can't unlock this file.")
    else:
        request.user.message_set.create(message = _(
                "Sorry, but you need to send a POST request."))
    try:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    except:
        return HttpResponseRedirect(reverse('component_detail',
            args=[project_slug, component_slug]))

@login_required
@one_perm_required_or_403(pr_component_lock_file, 
    (Project, 'slug__exact', 'project_slug'))
def component_file_lock(request, project_slug, component_slug, filename):
    if request.method == 'POST':

        component = get_object_or_404(Component, slug=component_slug,
                                    project__slug=project_slug)

        ctype = ContentType.objects.get_for_model(Component)

        pofile = get_object_or_404(POFile, object_id=component.pk, 
                                   content_type=ctype, filename=filename)

        try:
            POFileLock.objects.create_update(pofile, request.user)
            cache.delete(TFC_CACHING_PREFIX +'.component.'+component.full_name)
            request.user.message_set.create(
                message=_("Lock created. Please don't forget to remove it "
                "when you're done."))
        except POFileLockError, e:
            request.user.message_set.create(message=str(e))
    else:
       request.user.message_set.create(message = _(
           "Sorry, but you need to send a POST request."))

    try:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    except:
        return HttpResponseRedirect(reverse('component_detail',
            args=[project_slug, component_slug]))
