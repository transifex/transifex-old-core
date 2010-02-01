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
                "description": _("when an user request access to submit files " \
                                 "to a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_request_denied",
                "display": _("Submit access request to project denied"), 
                "description": _("when a maintainer denies access to an user " \
                                 "to submit files to a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_request_withdrawn",
                "display": _("Submit access request to project withdrawn"), 
                "description": _("when an user withdraws the access request" \
                                 "to submit files to a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_granted",
                "display": _("Submit access to project granted"), 
                "description": _("when a maintainer grants access to an user " \
                                 "to submit files to a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_revoked",
                "display": _("Submit access to project revoked"), 
                "description": _("when a maintainer revokes the access of an " \
                                 "user to submit files to a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_component_added",
                "display": _("New Component Added"), 
                "description": _("when a new component is added to a project"), 
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_component_changed",
                "display": _("Component Changed"), 
                "description": _("when a component of a project is changed"), 
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_component_deleted",
                "display": _("Component Deleted"), 
                "description": _("when a component of a project is deleted"), 
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_component_file_submitted",
                "display": _("File Submitted"), 
                "description": _("when a component file of a project"
                                 " is submitted"), 
                "default": 2,
                "show_to_user": False,
            },

            # Reviews

            {
                "label": "project_component_file_review_submitted",
                "display": _("File Review Submitted"), 
                "description": _("when a file of a component is submitted"
                                 " for review"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_component_file_changed",
                "display": _("Translation File Changed"),
                "description": _("when a component translation file of a"
                                 " project is changed"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_component_potfile_error",
                "display": _("Translation Source File (POT) has a Problem"),
                "description": _("when the source file (POT) of a"
                                 " component that you are a maintainer"
                                 " has a problem"), 
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
                "description" :_("when a release of a project is changed"), 
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
                "description": _("when a new translation team is added"
                                 " to a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_changed",
                "display": _("Team Changed"), 
                "description": _("when a translation team of a project"
                                 " is changed"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_deleted",
                "display": _("Team Deleted"), 
                "description": _("when a translation team of a project"
                                 " is deleted"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_requested",
                "display": _("Team Creation Requested"), 
                "description": _("when a translation team creation is requested"
                                 "for a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_request_denied",
                "display": _("Team Creation Request Denied"), 
                "description": _("when a translation team creation request"
                                 "for a project is denied by a maintainer"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_requested",
                "display": _("Team User Joining Requested"), 
                "description": _("when an user requests for joining to a"
                                 " translation team of a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_approved",
                "display": _("Team User Joining Approved"), 
                "description": _("when an user is approved as a member of a"
                                 " translation team of a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_denied",
                "display": _("Team User Joining Denied"), 
                "description": _("when an user is denied as a member of a"
                                 " translation team of a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_withdrawn",
                "display": _("Team User Joining Withdrawn"), 
                "description": _("when an user withdrawn its own request for"
                                 " joining a translation team of a project"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_left",
                "display": _("Team User Left"), 
                "description": _("when an user leaves a translation"
                                 " team of a project"), 
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
                "description": _("when an user nudges you"), 
                "default": 2,
                "show_to_user": True,
            },
    ]


def is_watched_by_user_signal(obj, user, signal=None):
    """
    Return a boolean value if an object is watched by an user or not

    It is possible also verify if it is watched by a user in a specific 
    signal, passing the signal as a second parameter
    """
    if signal:
        return is_observing(obj, user, signal)

    if isinstance(user, AnonymousUser):
        return False
    try:
        ctype = ContentType.objects.get_for_model(obj)
        observed_items = ObservedItem.objects.get(content_type=ctype,
                                                object_id=obj.id, user=user)
        return True
    except ObservedItem.DoesNotExist:
        return False
    except ObservedItem.MultipleObjectsReturned:
        return True


# Overwritting this function temporarily, until the upstream patch
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
