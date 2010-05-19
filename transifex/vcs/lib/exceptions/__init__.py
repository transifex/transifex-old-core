# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from txcommon.log import logger

class BaseVCSError(Exception):
    """
    Base Exception for all the VCS related exceptions that should be handled
    by the system and shown at the user interface in a clear way.

    This Exception is logged by default using logger.error().

    Attributes:
        original_exception -- Object/String related to the original exception.
    """
    # Some global settings
    message = "Gereric VCS error"
    user_message = _("Your request could not be completed. The admins have "
        "been notified to take a closer look at it. Please try again in a "
        "few minutes")
    notify_admins = True
    notify_maintainers = False

    def __init__(self, original_exception):
        self.original_exception = original_exception
        logger.error(self.__str__())

    def __str__(self):
        return repr('%s: %s' % (self.message, self.original_exception))

    def get_user_message(self, with_details=True):
        if with_details:
            return "%s Details from the VCS backend: '%s'." % (self.user_message, self.original_exception)
        else:
            return user_message

# General exceptions for errors of all VCSs
class SetupRepoError(BaseVCSError):
    message = "Local repository setup failed"
    user_message = _("Setup of the repository locally could not be done "
        "successfully.")
    notify_admins = False


class InitRepoError(BaseVCSError):
    message = "Local repository initialization failed"
    user_message = _("The local repository has not been setup yet. Please, "
        "first do a check-out of the repository.")
    notify_admins = False


class UpdateRepoError(BaseVCSError):
    message = "Update/Pull from remote repository failed"
    user_message = _("Unable to pull data from the remote repository. Is the"
        "remote host up?")
    notify_maintainers = True


class CleanupRepoError(BaseVCSError):
    message = "Cleanup of repository failed"
    user_message = _("Cleanup of the repository failed. The admins "
        "have been notified to take a closer look at it.")


class CommitRepoError(BaseVCSError):
    message = "Commit to repository failed"
    user_message = _("Commit to the repository failed.")


class PushRepoError(BaseVCSError):
    message = "Push to remote repository failed"
    user_message = _("Pushing to the remote repository failed.")
    notify_maintainers = True


class RevisionRepoError(BaseVCSError):
    message = "Given file does not have a revision"
    user_message = _("Given file does not have a revision. The admins "
        "have been notified to take a closer look at it.")

