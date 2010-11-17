import datetime
import inspect
from django.conf import settings
from django.core.cache import cache
from django.utils.hashcompat import md5_constructor
from django.utils.http import urlquote


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

def rl_last_update_now(resource, language):
    """
    This updates the cache value of last_update for a specific language of a
    resource with datetime.datetime.now(). Usefull when doing stuff that don't
    alter translation strings so that the last_update time will be updated.
    Also usefull when deleting translations.
    """

    cache.set(
        "cached_property_resources.resource:%(id)s_transifex.resources.stats"
        "_last_update_%(lang)s" % {'id': resource.id, 'lang': language.code},
        datetime.datetime.now())

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
        if cache.has_key(key):
            return cache.get(key)
        else:
            return cache_set(key, func(self))
    return property(cached_func)

def invalidate_object_cache(object, language=None):
    """
    Invalidate all cached properties of a specific object's stats. The only
    properties that are actually invalidated are those who belong to a Stats
    class. #FIXME: find a better way to handle invalidation for all classes.
    """
    return

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
    for lang,code in settings.LANGUAGES:
        cur_vars = list(variables)
        cur_vars.append(unicode(lang))
        args = md5_constructor(u':'.join([urlquote(var) for var in cur_vars]))
        cache_key = 'template.cache.%s.%s' % (fragment_name, args.hexdigest())
        cache.delete(cache_key)
