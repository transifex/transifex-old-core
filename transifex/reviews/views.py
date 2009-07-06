# -*- coding: utf-8 -*-
from polib import unescape

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.utils.translation import ugettext as _

from projects.models import Component
from translations.models import POFile
from reviews.models import POReviewRequest
from reviews.forms import POFileSubmissionForm


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


