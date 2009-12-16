# -*- coding: utf-8 -*-
import os
from polib import unescape

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.generic import create_update
from django.contrib.auth.decorators import login_required

from threadedcomments.forms import FreeThreadedCommentForm

from projects.models import Component
from reviews.models import POReviewRequest
from reviews.forms import (POFileSubmissionForm, AuthenticatedCommentForm)
from translations.models import POFile
from txcommon.lib.storage import save_file


def review_list(request, project_slug, component_slug):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)      
    form = POFileSubmissionForm()
    if request.user.is_authenticated():
        comment_form = AuthenticatedCommentForm(request.user)
    else:
        comment_form = FreeThreadedCommentForm()
    return render_to_response('reviews/review_list.html', {
        'component': component,
        'form': form,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))


def review_add(request, component_id):
    MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', '')

    component = get_object_or_404(Component, pk=component_id)
    if request.method == 'POST': # If the form has been submitted...
        form = POFileSubmissionForm(request.POST, request.FILES)
        if form.is_valid() and 'review_file' in request.FILES:
            file = request.FILES['review_file']
            r = POReviewRequest(author=request.user,
                                description=form.cleaned_data['description'],
                                file_name=os.path.basename(file.name),
                                component=component)
            r.save()
            target = os.path.join(settings.REVIEWS_ROOT, r.full_review_filename)
            save_file(target, file)
            return HttpResponseRedirect(
                reverse('review_list', args=[component.project.slug,
                                             component.slug]))
        else:
            return render_to_response('reviews/review_list.html', {
                'component': component,
                'form': form,
            }, context_instance=RequestContext(request))
    else:
        form = POFileSubmissionForm()
        
    return HttpResponseRedirect(
        reverse('review_list', args=[component.project.slug, component.slug]))


@login_required
#@perm_required_with_403('reviews.change_review')
def review_modify(request, id, *args, **kwargs):
    review_request = get_object_or_404(POReviewRequest, pk=id)
    if request.method == 'POST': # If the form has been submitted...
        if request.POST.has_key('accept'):
            review_request.resolution = 'A' # Accepted
            review_request.status = 'C' # Closed
            review_request.save()
            request.user.message_set.create(
                message=_("Request closed as Accepted."))
        elif request.POST.has_key('reject'):
            review_request.resolution = 'R' # Rejected
            review_request.status = 'C' # Closed
            review_request.save()
            request.user.message_set.create(
                message=_("Request closed as Rejected."))
        elif request.POST.has_key('reopen'):
            review_request.resolution = 'N' # Null
            review_request.status = 'O' # Opened
            review_request.save()
            request.user.message_set.create(
                message=_("Request reopened."))
        else:
            #FIXME: The admin should probably be notified for this.
            pass
    return HttpResponseRedirect(reverse('review_list',
        args=[review_request.component.project.slug,
              review_request.component.slug]))

