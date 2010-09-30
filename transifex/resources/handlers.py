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
from resources.stats import ResourceStatsList
from teams.models import Team

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
        invalidate_template_cache("resource_details",
            resource.project.slug, resource.slug,
             lang.code)

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



