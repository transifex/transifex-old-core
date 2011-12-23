# -*- coding: utf-8 -*-
import copy
import itertools
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db import transaction
from django.dispatch import Signal
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from actionlog.models import action_logging
from transifex.languages.models import Language
from notification import models as notification
from transifex.projects.models import Project, HubRequest
from transifex.projects.permissions import *
from transifex.resources.models import RLStats
# Temporary
from transifex.txcommon import notifications as txnotification

from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger
from transifex.txcommon.views import (json_result, json_error)


pr_hub_add_project_perm=(("granular", "project_perm.maintain"),)
@login_required
@one_perm_required_or_403(pr_hub_add_project_perm,
    (Project, "slug__exact", "project_slug"),
    (Language, "code__exact", "language_code"))
@transaction.commit_on_success
def hub_join_approve(request, project_slug, project_slug_requester):

    team = get_object_or_404(Team, project__slug=project_slug,
        language__code=language_code)
    project = team.project
    user = get_object_or_404(User, username=username)
    access_request = get_object_or_404(TeamAccessRequest, team__pk=team.pk,
        user__pk=user.pk)

    if request.POST:
        if user in team.members.all() or \
            user in team.coordinators.all():
            messages.warning(request,
                            _("User '%(user)s' is already on the '%(team)s' team.")
                            % {'user':user, 'team':team.language.name})
            access_request.delete()
        try:
            team.members.add(user)
            team.save()
            messages.success(request,
                            _("You added '%(user)s' to the '%(team)s' team.")
                            % {'user':user, 'team':team.language.name})
            access_request.delete()

            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_team_join_approved'
            context = {'access_request': access_request}

            # Logging action
            action_logging(request.user, [project, team], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for those that are observing this project
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
                # Send notification for maintainers, coordinators and the user
                notification.send(set(itertools.chain(project.maintainers.all(),
                    team.coordinators.all(), [access_request.user])), nt, context)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

    return HttpResponseRedirect(reverse("team_detail",
                                        args=[project_slug, language_code]))


pr_team_deny_member_perm=(("granular", "project_perm.coordinate_team"),)
@login_required
@one_perm_required_or_403(pr_team_deny_member_perm,
    (Project, "slug__exact", "project_slug"),
    (Language, "code__exact", "language_code"))
@transaction.commit_on_success
def team_join_deny(request, project_slug, language_code, username):

    team = get_object_or_404(Team, project__slug=project_slug,
        language__code=language_code)
    project = team.project
    user = get_object_or_404(User, username=username)
    access_request = get_object_or_404(TeamAccessRequest, team__pk=team.pk,
        user__pk=user.pk)

    if request.POST:
        try:
            access_request.delete()
            messages.info(request,_(
                "You rejected the request by user '%(user)s' to join the "
                "'%(team)s' team."
                ) % {'user':user, 'team':team.language.name})

            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_team_join_denied'
            context = {'access_request': access_request,
                       'performer': request.user,}

            # Logging action
            action_logging(request.user, [project, team], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for those that are observing this project
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
                # Send notification for maintainers, coordinators and the user
                notification.send(set(itertools.chain(project.maintainers.all(),
                    team.coordinators.all(), [access_request.user])), nt, context)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

    return HttpResponseRedirect(reverse("team_detail",
                                        args=[project_slug, language_code]))


@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'))
@transaction.commit_on_success
def team_join_withdraw(request, project_slug, language_code):

    team = get_object_or_404(Team, project__slug=project_slug,
        language__code=language_code)
    project = team.project
    access_request = get_object_or_404(TeamAccessRequest, team__pk=team.pk,
        user__pk=request.user.pk)

    if request.POST:
        try:
            access_request.delete()
            messages.success(request,_(
                "You withdrew your request to join the '%s' team."
                ) % team.language.name)

            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_team_join_withdrawn'
            context = {'access_request': access_request,
                       'performer': request.user,}

            # Logging action
            action_logging(request.user, [project, team], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for those that are observing this project
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
                # Send notification for maintainers, coordinators
                notification.send(set(itertools.chain(project.maintainers.all(),
                    team.coordinators.all())), nt, context)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

    return HttpResponseRedirect(reverse("team_detail",
                                        args=[project_slug, language_code]))


@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'))
@transaction.commit_on_success
def team_leave(request, project_slug, language_code):

    team = get_object_or_404(Team, project__slug=project_slug,
        language__code=language_code)
    project = team.project

    if request.POST:
        try:
            if request.user in team.members.all():
                team.members.remove(request.user)
                messages.info(request, _(
                    "You left the '%s' team."
                    ) % team.language.name)

                # ActionLog & Notification
                # TODO: Use signals
                nt = 'project_team_left'
                context = {'team': team,
                        'performer': request.user,}

                # Logging action
                action_logging(request.user, [project, team], nt, context=context)

                if settings.ENABLE_NOTICES:
                    # Send notification for those that are observing this project
                    txnotification.send_observation_notices_for(project,
                            signal=nt, extra_context=context)
                    # Send notification for maintainers, coordinators
                    notification.send(set(itertools.chain(project.maintainers.all(),
                        team.coordinators.all())), nt, context)
            else:
                messages.info(request, _(
                    "You are not in the '%s' team."
                    ) % team.language.name)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

    return HttpResponseRedirect(reverse("team_detail",
                                        args=[project_slug, language_code]))



@login_required
@one_perm_required_or_403((("granular", "project_perm.maintain"),),
    (Project, "slug__exact", "project_slug"),)
def hub_associate_project_toggler(request, project_slug):

    project = get_object_or_404(Project, slug=project_slug)

    if request.method != 'POST':
        return json_error(_('Must use POST to activate'))

    print request.POST

    outsourced_project_slug = request.POST.get('outsourced_project_slug', None)
    if not outsourced_project_slug:
        return json_error(_('Bad request.'))

    url = reverse('hub_associate_project_toggler', args=(project_slug,))
    
    try:
        
        outsourced_project = project.outsourcing.get(slug=outsourced_project_slug)
        outsourced_project.outsource = None
        outsourced_project.save()

        ## ActionLog & Notification
        #nt = 'project_hub_added'
        #context = {'team': team}

        ## Logging action
        #action_logging(request.user, [project, team], nt, context=context)

        #if settings.ENABLE_NOTICES:
            ## Send notification for those that are observing this project
            #txnotification.send_observation_notices_for(project,
                    #signal=nt, extra_context=context)
            ## Send notification for maintainers and coordinators
            #notification.send(set(itertools.chain(project.maintainers.all(),
                #team.coordinators.all())), nt, context)

        result = {
            'style': 'undo',
            'title': _('Undo'),
            'outsourced_project_slug': outsourced_project_slug,
            'url': url,
            'error': None,
        }

    except Project.DoesNotExist:

        outsourced_project = get_object_or_404(Project, 
            slug=outsourced_project_slug)
        outsourced_project.outsource = project
        outsourced_project.save()

        result = {
            'style': 'connect',
            'title': _('Disassociate it'),
            'outsourced_project_slug': outsourced_project_slug,
            'url': url,
            'error': None,
        }

    except Exception, e:
        return json_error(e.message, result)

    return json_result(result)





