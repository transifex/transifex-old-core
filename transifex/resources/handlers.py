# -*- coding: utf-8 -*-
from hashlib import md5
from django.core.cache import cache
from django.conf import settings
from django.utils.hashcompat import md5_constructor
from django.utils.http import urlquote
from actionlog.models import action_logging
from projects.signals import post_resource_save, post_resource_delete
from txcommon import notifications as txnotification
from resources import CACHE_KEYS as RESOURCES_CACHE_KEYS
from resources.utils import invalidate_object_cache
from teams.models import Team

def on_ss_save_invalidate_cache(sender, instance, created, **kwargs):
    """Invalidate cache keys related to the SourceEntity updates"""

    if created:
        invalidate_object_cache(instance.resource)
        # Number of source strings in resource
        for lang in instance.resource.available_languages:
            team = Team.objects.get_or_none(instance.resource.project, lang.code)
            if team:
                # Template lvl cache for team details
                invalidate_template_cache("team_details",
                    team.id, instance.resource.id)

            for rel in instance.resource.project.releases.all():
                # Template lvl cache for release details
                invalidate_template_cache("release_details",
                    rel.id, lang.id)

            # Template lvl cache for resource details
            invalidate_template_cache("resource_details",
                instance.resource.project.slug, instance.resource.slug,
                 lang.code)


def on_ss_delete_invalidate_cache(sender, instance, **kwargs):
    """Invalidate cache keys related to the SourceEntity updates"""
    if instance and instance.resource and instance.resource.project:
        invalidate_object_cache(instance.resource)

        for lang in instance.resource.available_languages:
            team = Team.objects.get_or_none(instance.resource.project, lang.code)
            if team:
                # Template lvl cache for team details
                invalidate_template_cache("team_details",
                    team.id, instance.resource.id)

            for rel in instance.resource.project.releases.all():
                # Template lvl cache for release details
                invalidate_template_cache("release_details",
                    rel.id, lang.id)

            # Template lvl cache for resource details
            invalidate_template_cache("resource_details",
                instance.resource.project.slug, instance.resource.slug,
                lang.code)

def on_ts_save_invalidate_cache(sender, instance, created, **kwargs):
    """
    Invalidation for Translation save()

    Here we handle the following:
     - Invalidate the teplate level cache for the Translation language
     - Invalidate the translated_strings for this resource/language
     - Invalidate the last_updated property for this language
    """

    if created:
        invalidate_object_cache(instance.source_entity.resource)

        team = Team.objects.get_or_none(instance.source_entity.resource.project,
            instance.language.code)
        if team:
            # Invalidate team details template cache for this lang
            invalidate_template_cache("team_details",
                team.id, instance.source_entity.resource.id)

        for rel in instance.source_entity.resource.project.releases.all():
            # Invalidate release details template cache for this lang
            invalidate_template_cache("release_details",
                rel.id, instance.language.id)

        # Invalidate resource details template cache for this lang
        invalidate_template_cache("resource_details",
            instance.source_entity.resource.project.slug,
            instance.source_entity.resource.slug, instance.language.code)

def on_ts_delete_invalidate_cache(sender, instance, **kwargs):
    """
    Invalidation for Translation delete()

    Here we handle the following:
     - Invalidate the template level cache for the resource/language
     - Invalidate the translated_stings for the resource/language
     - Invalidate the last_updated property for this language
    """
    invalidate_object_cache(instance.source_entity.resource)

    team = Team.objects.get_or_none(instance.source_entity.resource.project,
        instance.language.code)
    if team:
        # Invalidate team details template cache for this lang
        invalidate_template_cache("team_details",
            team.id, instance.source_entity.resource.id)

    for rel in instance.source_entity.resource.project.releases.all():
        # Invalidate release details template cache for this lang
        invalidate_template_cache("release_details",
            rel.id, instance.language.id)

def invalidate_template_cache(fragment_name, *variables):
    """
    This function invalidates a template cache named `fragment_name` and with
    variables which are included in *variables. For example:

    {% cache 500 project_details project.slug %}
        ...
    {% endcache %}

    We invalidate this by calling:
     -  invalidate_template_cache("project_details", project.slug)
    """
    args = md5_constructor(u':'.join([urlquote(var) for var in variables]))
    cache_key = 'template.cache.%s.%s' % (fragment_name, args.hexdigest())
    cache.delete(cache_key)

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



