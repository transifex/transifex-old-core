# -*- coding: utf-8 -*-
from hashlib import md5
from django.core.cache import cache
from django.conf import settings
from actionlog.models import action_logging
from projects.signals import post_resource_save, post_resource_delete
from txcommon import notifications as txnotification
from happix.models import HAPPIX_CACHE_KEYS

# FIXME we can do more clever calculations instead of deleting the values
# FIXME: if resource/project doesn't exist cache doesn't clear. maybe force
# expire?
def on_save_invalidate_cache(sender, instance, created, **kwargs):
    """Invalidate cache keys related to the SourceEntity updates"""
    if instance and instance.resource and instance.resource.project:
        cache.delete(HAPPIX_CACHE_KEYS["word_count"] % (instance.resource.project.slug,
            instance.resource.slug))
        if created:
            cache.delete(HAPPIX_CACHE_KEYS["source_strings_count"]% (
                instance.resource.project.slug,
                instance.resource.slug))


def on_delete_invalidate_cache(sender, instance, **kwargs):
    """Invalidate cache keys related to the SourceEntity updates"""
    if instance and instance.resource and instance.resource.project:
        cache.delete(HAPPIX_CACHE_KEYS["word_count"] % (instance.resource.project.slug,
            instance.resource.slug))
        cache.delete(HAPPIX_CACHE_KEYS["source_strings_count"]% (
            instance.resource.project.slug,
            instance.resource.slug))



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
