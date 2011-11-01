# -*- coding: utf-8 -*-

"""
Handlers for the addon.
"""

import requests
from django.db.models import get_model
from webhooks.models import WebHook
from transifex.txcommon.log import logger
from transifex.resources.signals import post_update_rlstats


def visit_url(sender, **kwargs):
    """Visit the URL for the project.

    Send the slug of the project, the slug of the resource and the language
    of the translation as identifiers. Send the translation percentage
    as information.

    Args:
        sender: The rlstats object itself.
    Returns:
        True of False for success (or not).
    """
    # TODO make it a celery task
    # TODO increase the timeout in celery

    stats = sender
    resource = stats.resource
    project = resource.project
    language = stats.language

    if 'post_function' in kwargs:
        post_function = kwargs['post_function']
    else:
        post_function = requests.post

    try:
        hook = WebHook.objects.get(project=project)
    except WebHook.DoesNotExist:
        logger.debug("Project %s has no web hooks" % project.slug)
        return False

    event_info = {
        'project': project.slug,
        'resource': resource.slug,
        'language': language.code,
        'percent': stats.translated_perc,
    }
    logger.debug(
        "POST data for %s: %s" % (stats.resource.project.slug, event_info)
    )

    res = post_function(
        hook.url, data=event_info, allow_redirects=False, timeout=2.0
    )
    if res.ok:
        logger.debug("POST for project %s successful." % project)
        return True
    else:
        msg = "Error visiting webhook %s: HTTP code is %s" % (
            hook, res.status_code
        )
        logger.error(msg)
        return False


def connect():
    # TODO catch other cases, too (eg project.pre_delete
    post_update_rlstats.connect(visit_url)
