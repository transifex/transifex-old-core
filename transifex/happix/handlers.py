# -*- coding: utf-8 -*-
from django.core.cache import cache

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



