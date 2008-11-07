import os
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import create_update, list_detail
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import feed

from txcollections.models import Collection

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


# Collections

# Override generic views to use decorator

@login_required
def collection_create(*args, **kwargs):
    return create_update.create_object(*args, **kwargs)

@login_required
def collection_update(*args, **kwargs):
    return create_update.update_object(*args, **kwargs)

@login_required
def collection_delete(*args, **kwargs):
    return create_update.delete_object(*args, **kwargs)