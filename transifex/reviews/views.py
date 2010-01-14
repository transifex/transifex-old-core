# -*- coding: utf-8 -*-
import os
from polib import unescape

from django.core.files.uploadedfile import InMemoryUploadedFile
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
from reviews.models import POReviewRequest, ReviewLike
from reviews.forms import (POFileSubmissionForm, AuthenticatedCommentForm)
from translations.models import POFile
from txcommon.lib.storage import save_file


@login_required
def review_like(request, id, *args, **kwargs):
    review_request = get_object_or_404(POReviewRequest, pk=id)
    if request.method == 'POST': # If the form has been submitted...
            r, created = ReviewLike.objects.get_or_create(reviewrequest=review_request, user=request.user)
            if request.POST.has_key("like") and request.POST["like"]=="like":
                r.like=True
                r.save()
            elif request.POST.has_key("dislike") and request.POST["dislike"]=="dislike":
                r.like=False
                r.save()
    return HttpResponseRedirect(reverse('review_list',
        args=[review_request.component.project.slug,
              review_request.component.slug]))


def review_list(request, project_slug, component_slug):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)      
    if request.user.is_authenticated():
        comment_form = AuthenticatedCommentForm(request.user)
    else:
        comment_form = FreeThreadedCommentForm()
    return render_to_response('reviews/review_list.html', {
        'component': component,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))


def review_add_common(request, component, submitted_file, form=None, filename=None, lang_code=None):
    """ Common functionality wrapper."""
    if not submitted_file:
        request.user.message_set.create(message=_("Please select a " 
                            "file from your system to be uploaded."))
    else:
        if form:
            description = form.cleaned_data['description'] 
        elif request.POST.get('message', None):
            description = request.POST.get('message')
        else: # FIXME: Default review description. Tied as hell.
            description = 'Translation review request for \'%s\' of the ' \
                          '\'%s\' component' % (filename, component)
        r = POReviewRequest(author=request.user,
                            description=description,
                            file_name=os.path.basename(submitted_file.name),
                            target_filename=filename,
                            lang_code=lang_code,
                            component=component)
        r.save()
        target = os.path.join(settings.REVIEWS_ROOT, r.full_review_filename)
        save_file(target, submitted_file)
        request.user.message_set.create(message=_("Your file has been "
            "successfully placed for reviewing."))
    return HttpResponseRedirect(
        reverse('review_list', args=[component.project.slug,
                                        component.slug]))

def review_add(request, component_id):
    """This method will be used to provide a separate form for review uploading."""

    MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', '')
    component = get_object_or_404(Component, pk=component_id)
    if request.method == 'POST': # If the form has been submitted...

        form = POFileSubmissionForm(request.POST, request.FILES)

        if form.is_valid() and 'review_file' in request.FILES:
            return review_add_common(request, component, request.FILES['review_file'], form)
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
    #FIXME: To avoid import this call we should create a wrapper
    from projects.views.component import component_submit_file

    review_request = get_object_or_404(POReviewRequest, pk=id)
    if request.method == 'POST': # If the form has been submitted...
        if request.POST.has_key('accept'):
            review_request.resolution = 'A' # Accepted
            review_request.status = 'C' # Closed
            review_request.save()
            #FIXME: The file should be handled with another wrapper!
            redirection = component_submit_file(request,
                 review_request.component.project.slug,
                 review_request.component.slug, 
                 filename=review_request.target_filename,
                 submitted_file=InMemoryUploadedFile(
                 open(review_request.file_path,'r'),
                 'submitted_file',
                 review_request.file_path,
                 'text/x-gettext-translation',
                 os.path.getsize(review_request.file_path),None))
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

