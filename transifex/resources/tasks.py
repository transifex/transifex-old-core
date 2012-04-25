#from celery.decorators import task
from notification import models as notification

from django.conf import settings
from transifex.txcommon.log import logger


#@task(name='tx_project_resource_full_reviewed', ignore_result=True, max_retries=3)
def check_and_notify_resource_full_reviewed(**kwargs):
    """
    Handler to notify maintainers about 100% reviewed translations.
    """ 
    rlstats = kwargs.pop('sender')
    if (settings.ENABLE_NOTICES and 
        rlstats.resource.source_language != rlstats.language):

        logger.debug("resource: Checking if resource translation is fully "
            "reviewed: %s (%s)" % (rlstats.resource, rlstats.language.code))

        if rlstats.reviewed_perc == 100:
            logger.debug("resource: Resource translation is fully reviewed.")

            # Notification
            context = {
                'project': rlstats.resource.project,
                'resource': rlstats.resource,
                'language': rlstats.language,}
            nt = "project_resource_full_reviewed"

            notification.send(rlstats.resource.project.maintainers.all(),
                nt, context)


@task(name='send_notices_on_resource_changed', max_retries=2)
def send_notices_for_resource_edited(resource, user):
    """
    Send notifications, when a resource has been edited.

    Args:
        resource: The resource that has been edited.
        user: The user that did the update.
    """
    post_resource_save.send(
        sender=None, instance=resource, created=False, user=user
    )
