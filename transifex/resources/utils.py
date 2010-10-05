import inspect
from django.core.cache import cache


def key_from_instance(instance):
    """
    Returns a key from an object instance that is unique and can be used as a
    caching key.
    """
    opts = instance._meta
    return '%s.%s:%s' % (opts.app_label, opts.module_name, instance.pk)

def cache_set(key, value):
    """
    Similar to cache.set only it returns the value as well. Useful when you
    want to do something like this:

    # return cache.set(key,value)
    """
    cache.set(key, value)
    return value

def stats_cached_property(func):
    """
    A method decorator that does the same thing as the @property with added
    caching for the return value of the method. They key used for the caching
    is handcrafted and suited only for Stats/StatsBase/StatsList classes so
    it's not very reusable.
    """
    def cached_func(self):
        if not self.object:
            return func(self)

        if hasattr(self, "language") and self.language:
            key = 'cached_property_%s_%s_%s_%s' % \
                (key_from_instance(self.object), func.__module__,
                func.__name__, self.language.code )
        else:
            key = 'cached_property_%s_%s_%s' % \
                (key_from_instance(self.object), func.__module__, func.__name__)
        return cache.get(key) or cache_set(key, func(self))
    return property(cached_func)

def invalidate_object_cache(object, language=None):
    """
    Invalidate all cached properties of a specific object's stats. The only
    properties that are actually invalidated are those who belong to a Stats
    class. #FIXME: find a better way to handle invalidation for all classes.
    """
    # !important: If you change the import path to include transifex (eg
    # transifex.resources.stats) this will BREAK caching since the keys that
    # are being created don't have the full path of the module. If you need to
    # change this import statement then you NEED to change the
    # stats_cached_property as well.
    from resources.stats import Stats, StatsBase

    keys = []
    for name, type in inspect.getmembers(StatsBase):
        if type.__class__.__name__ == "property":
            keys.append("_".join([Stats.__module__, name]))

    if language:
        for name, type in inspect.getmembers(Stats):
            if type.__class__.__name__ == "property":
                keys.append("_".join([StatsBase.__module__, name, language.code]))

    for key in keys:
        cache.delete("cached_property_%s_%s" % (key_from_instance(object), key))
