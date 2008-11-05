import os
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import list_detail
from django.utils.translation import ugettext_lazy as _
from django.contrib.syndication.views import feed

from projects.models import Component
from models import Language


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


def language_detail(request, slug, *args, **kwargs):
    language = get_object_or_404(Language, code__iexact=slug)
    component_list = Component.objects.with_language(language)
    return list_detail.object_detail(
        request,
        object_id=language.id,
        extra_context = {'component_list': component_list},
        *args, **kwargs
    )
language_detail.__doc__ = list_detail.object_detail.__doc__
