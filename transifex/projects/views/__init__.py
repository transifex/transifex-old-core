from django.contrib.syndication.views import feed

# Feeds
def slug_feed(request, slug=None, param='', feed_dict=None):
    """
    Override default feed, using custom (including inexistent) slug.
    
    Provides the functionality needed to decouple the Feed's slug from
    the urlconf, so a feed mounted at "^/feed" can exist.
    
    See also http://code.djangoproject.com/ticket/6969.
    """
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)


# Release
def release_feed(request, project_slug, release_slug, slug=None, param='', 
    feed_dict=None,):
    param = '%s/%s' % (project_slug, release_slug)
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)


def release_language_feed(request, project_slug, release_slug, language_code,
    slug=None, param='', feed_dict=None,):
    param = '%s/%s/%s' % (project_slug, release_slug, language_code)
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)