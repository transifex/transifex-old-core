# -*- coding: utf-8 -*-
import os
import itertools
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

from authority.views import permission_denied
from notification import models as notification
from threadedcomments.forms import FreeThreadedCommentForm

from actionlog.models import action_logging
from languages.models import Language
from projects.models import Component
from projects.permissions.project import ProjectPermission
from projects.views.component import component_submit_file
from reviews.models import POReviewRequest, ReviewLike
from reviews.forms import (POFileSubmissionForm, AuthenticatedCommentForm)
from teams.models import Team
from translations.models import POFile
from txcommon.decorators import one_perm_required_or_403
from txcommon.lib.storage import save_file


@login_required
def review_modify(request, project_slug, component_slug, id):

    review_request = get_object_or_404(POReviewRequest, pk=id)
    project = review_request.component.project

    # Check permissions
    check = ProjectPermission(request.user)
    if not check.submit_file(review_request.team or project) and not \
        request.user.has_perm('reviews.change_poreviewrequest'):
        return permission_denied(request)

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
                    os.path.getsize(review_request.file_path), None))
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
            logger.debug('Ops! A POST request was sent to modify the review '
                'number %s, but no valid action was passed.' % review.id)
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

