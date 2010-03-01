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

from actionlog.models import action_logging
from notification import models as notification
from threadedcomments.forms import FreeThreadedCommentForm

from languages.models import Language
from projects.models import Component
from reviews.models import POReviewRequest, ReviewLike
from teams.models import Team
from translations.models import POFile
from txcommon.lib.storage import save_file


@login_required
def review_add(request, component, submitted_file, language=None):
    """ Common functionality wrapper."""

    if not language:
        request.user.message_set.create(message=_("You can upload a file " 
            "for review only if it's related to an existing language."))
    else:
        filename = submitted_file.targetfile
        if request.POST.get('message', None):
            description = request.POST.get('message')
        else: # FIXME: Default review description. Tied as hell.
            description = "Translation review request for '%(filename)s' of " \
                          "the '%(component)s' component" \
                          % {'filename':filename, 'component':component}

        r = POReviewRequest(author=request.user,
                            description=description,
                            file_name=os.path.basename(submitted_file.name),
                            target_filename=filename,
                            lang_code=language.code,
                            component=component)
        r.save()
        target = os.path.join(settings.REVIEWS_ROOT, r.full_review_filename)
        save_file(target, submitted_file)
        request.user.message_set.create(message=_("Your file has been "
            "successfully placed for reviewing."))

        # ActionLog & Notification
        # TODO: Use signals
        object_list = [component.project, component, language]
        team = Team.objects.get_or_none(component.project, language.code)
        if team:
            object_list.append(team)
            send_notification_to = itertools.chain(team.members.all(),
                team.coordinators.all())
        else:
            send_notification_to = component.project.maintainers.all()

        nt = 'project_component_file_review_submitted'
        context = {'component': component,
                   'filename': filename,
                   'language': language}
        action_logging(request.user, object_list, nt, context=context)
        if settings.ENABLE_NOTICES:
            notification.send(send_notification_to, nt, context)
        return HttpResponseRedirect(
            reverse('review_list', args=[component.project.slug,
                                        component.slug]))

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

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


