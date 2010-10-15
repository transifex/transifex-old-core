# -*- coding: utf-8 -*-
from django.conf import settings
from actionlog.models import action_logging
from transifex.projects.signals import post_resource_save, post_resource_delete
from transifex.txcommon import notifications as txnotification
from transifex.resources import CACHE_KEYS as RESOURCES_CACHE_KEYS
from transifex.resources.utils import (invalidate_object_cache,
    invalidate_template_cache)
from transifex.resources.stats import ResourceStatsList
from transifex.teams.models import Team

def invalidate_stats_cache(resource, language=None, **kwargs):
    """Invalidate cache keys related to the SourceEntity updates"""
    invalidate_object_cache(resource, language)

    invalidate_object_cache(resource.project, language)

    for rel in resource.project.releases.all():
        invalidate_object_cache(rel, language)

    if not language:
        stats = ResourceStatsList(resource)
        langs = stats.available_languages
    else:
        langs = [language]

    # Template lvl cache for resource details
    invalidate_template_cache("resource_details",
        resource.project.slug, resource.slug)

    invalidate_template_cache("project_resource_details",
        resource.project.slug, resource.slug)

    # Number of source strings in resource
    for lang in langs:
        team = Team.objects.get_or_none(resource.project, lang.code)
        if team:
            # Template lvl cache for team details
            invalidate_template_cache("team_details",
                team.id, resource.id)

        for rel in resource.project.releases.all():
            # Template lvl cache for release details
            invalidate_template_cache("release_details",
                rel.id, lang.id)

        # Template lvl cache for resource details
        invalidate_template_cache("resource_details_lang",
            resource.project.slug, resource.slug,
             lang.code)

def on_resource_save(sender, instance, created, user, **kwargs):
    """
    Called on resource post save and passes a user object in addition to the
    saved instance. Used for logging the create/update of a resource.
    """
    # ActionLog & Notification
    context = {'resource': instance}
    object_list = [instance.project, instance]
    if created:
        nt = 'project_resource_added'
        action_logging(user, object_list, nt, context=context)
        if settings.ENABLE_NOTICES:
            txnotification.send_observation_notices_for(instance.project,
                    signal=nt, extra_context=context)
    else:
        nt = 'project_resource_changed'
        action_logging(user, object_list, nt, context=context)
        if settings.ENABLE_NOTICES:
            txnotification.send_observation_notices_for(instance.project,
                    signal=nt, extra_context=context)

def on_resource_delete(sender, instance, user,**kwargs):
    """
    Called on resource post delete to file an action log for this action.
    Passes a user object along with the deleted instance for use in the logging
    mechanism.
    """
    # ActionLog & Notification
    context = {'resource': instance}
    object_list = [instance.project, instance]
    nt = 'project_resource_deleted'
    action_logging(user, object_list, nt, context=context)
    if settings.ENABLE_NOTICES:
        txnotification.send_observation_notices_for(instance.project,
                signal=nt, extra_context=context)


# Resource signal handlers for logging
post_resource_save.connect(on_resource_save)
post_resource_delete.connect(on_resource_delete)



