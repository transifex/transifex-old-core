# -*- coding: utf-8 -*-
from django.conf import settings

from lotte.signals import lotte_done
from transifex.projects.signals import post_submit_translation
from transifex.txcommon import notifications as txnotification
from transifex.txcommon.log import logger

from models import TranslationWatch

def _notify_translationwatchers(resource, language):
    """
    Notify the watchers for a specific TranslationWatch
    """
    context = {
        'project': resource.project,
        'resource': resource,
        'language': language,
    }

    twatch = TranslationWatch.objects.get_or_create(resource=resource,
        language=language)[0]

    logger.debug("addon-watches: Sending notification for '%s'" % twatch)
    txnotification.send_observation_notices_for(twatch,
        signal='project_resource_translation_changed', extra_context=context)


def lotte_done_handler(sender, request, resources, language, modified,
    **kwargs):
    if modified and settings.ENABLE_NOTICES:
        for resource in resources:
            _notify_translationwatchers(resource, language)


def post_submit_translation_handler(sender, request, resource, language,
    modified, **kwargs):
    if modified and settings.ENABLE_NOTICES:
        _notify_translationwatchers(resource, language)

def connect():
    lotte_done.connect(lotte_done_handler)
    post_submit_translation.connect(post_submit_translation_handler)
