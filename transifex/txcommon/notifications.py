# -*- coding: utf-8 -*-
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_noop as _
from notification.models import ObservedItem, is_observing, send


# This is temporary
NOTICE_TYPES = [
            {
                "label": "project_added",
                "display": _("New Project Added"),
                "description": _("when a new project is added"),
                "default": 1,
                "show_to_user": False,
            },
            {
                "label": "project_changed",
                "display": _("Project Changed"),
                "description": _("when a project is changed"),
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_deleted",
                "display": _("Project Deleted"),
                "description": _("when a project is deleted"),
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_requested",
                "display": _("Submit access to project requested"),
                "description": _("when a user request access to submit files "
                                 "to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_request_denied",
                "display": _("Submit access request to project denied"),
                "description": _("when a maintainer denies a user access "
                                 "to submit files to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_request_withdrawn",
                "display": _("Submit access request to project withdrawn"),
                "description": _("when a user withdraws the request for "
                                 "access to submit files to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_granted",
                "display": _("Submit access to project granted"),
                "description": _("when a maintainer grants a user access "
                                 "to submit files to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_revoked",
                "display": _("Submit access to project revoked"),
                "description": _("when a maintainer revokes the access of an "
                                 "user to submit files to a project"),
                "default": 2,
                "show_to_user": True,
            },

            # Project releases

            {
                "label": "project_release_added",
                "display": _("New Release Added for a Watched Project"),
                "description": _("when a new release is added to a project"),
                "default": 2,
                "show_to_user": False,
            },
            {
                "label": "project_release_changed",
                "display": _("Release Changed"),
                "description": _("when a release of a project is changed"),
                "default": 1,
                "show_to_user": False,
            },
            {   "label": "project_release_deleted",
                "display": _("Release Deleted"),
                "description": _("when a release of a project is deleted"),
                "default": 1,
                "show_to_user": False,
            },
            {   "label": "project_release_added",
                "display": _("Release Added to a Project"),
                "description": _("when a release is added to a project"),
                "default": 2,
                "show_to_user": False,
            },
            {   "label": "project_release_deleted",
                "display": _("Release Deleted from a Project"),
                "description": _("when a release is deleted from a project"),
                "default": 2,
                "show_to_user": False,
            },

            # Teams

            {
                "label": "project_team_added",
                "display": _("New Team Added"),
                "description": _("when a new translation team is added "
                                 "to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_changed",
                "display": _("Team Changed"),
                "description": _("when a translation team of a project "
                                 "is changed"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_deleted",
                "display": _("Team Deleted"),
                "description": _("when a translation team of a project "
                                 "is deleted"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_requested",
                "display": _("Team Creation Requested"),
                "description": _("when a translation team creation is requested "
                                 "for a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_request_denied",
                "display": _("Team Creation Request Denied"),
                "description": _("when a translation team creation request "
                                 "for a project is denied by a maintainer"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_requested",
                "display": _("Team User Joining Requested"),
                "description": _("when a user requests to join a "
                                 "project translation team"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_approved",
                "display": _("Team User Joining Approved"),
                "description": _("when a user is approved as a member of a "
                                 "project translation team"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_denied",
                "display": _("Team User Joining Denied"),
                "description": _("when a user is denied as a member of a "
                                 "project translation team"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_withdrawn",
                "display": _("Team User Joining Withdrawn"),
                "description": _("when a user decides not to "
                                 "join a project translation team"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_left",
                "display": _("Team User Left"),
                "description": _("when a user leaves a "
                                 "project translation team"),
                "default": 2,
                "show_to_user": True,
            },

            # Reports

            {
                "label": "project_report_weekly_maintainers",
                "display": _("Weekly project report for maintainers"),
                "description": _("when you receive the weekly report of "
                                 "projects that you maintain."),
                "default": 2,
                "show_to_user": True,
            },

            {   "label": "user_nudge",
                "display": _("User Nudge"),
                "description": _("when a user nudges you"),
                "default": 2,
                "show_to_user": True,
            },

            # Resources

            {
                "label": "project_resource_added",
                "display": _("Resource Added"),
                "description": _("when a new resource is added to a project"),
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_resource_changed",
                "display": _("Resource Changed"),
                "description": _("when a resource of a project is changed"),
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_resource_deleted",
                "display": _("Resource Deleted"),
                "description": _("when a resource of a project is deleted"),
                "default": 1,
                "show_to_user": True,
            },
            {   # Used only for ActionLog purposes.
                "label": "project_resource_translated",
                "display": _("Resource Translated"),
                "description": _("when a translation is sent to a project "
                    "resource"),
                "default": 0,
                "show_to_user": False,
            },
            {
                "label": "project_resource_translation_changed",
                "display": _("Resource Translation Changed"),
                "description": _("when a resource translation you are "
                    "watching changes"),
                "default": 0,
                "show_to_user": True,
            },
    ]


# Overwriting this function temporarily, until the upstream patch
# http://github.com/jezdez/django-notification/commit/a8eb0980d2f37b799ff55dbc3a386c97ad479f99
# be accepted on http://github.com/pinax/django-notification
def send_observation_notices_for(observed, signal='post_save', extra_context=None):
    """
    Send a notice for each registered user about an observed object.
    """
    observed_items = ObservedItem.objects.all_for(observed, signal)
    for item in observed_items:
        if extra_context is None:
            extra_context = {}

        context = {
            "observed": item.observed_object,
        }
        context.update(extra_context)

        send([item.user], item.notice_type.label, context)
    return observed_items
