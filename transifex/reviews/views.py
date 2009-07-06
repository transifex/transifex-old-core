# -*- coding: utf-8 -*-
from polib import unescape

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.generic import create_update
from django.contrib.auth.decorators import login_required

from projects.models import Component
from reviews.models import POReviewRequest
from reviews.forms import POFileSubmissionForm
from translations.models import POFile

def review_list(request, project_slug, component_slug):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    reviews = POReviewRequest.open_reviews.all()
    if request.method == 'POST': # If the form has been submitted...
        form = POFileSubmissionForm(request.POST)
    else:
        form = POFileSubmissionForm()
        
    return render_to_response('reviews/review_list.html', {
        'component': component,
        'form': form,
        'reviews': reviews,
    }, context_instance=RequestContext(request))


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

