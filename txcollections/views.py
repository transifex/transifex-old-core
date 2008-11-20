import os
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import create_update, list_detail
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import feed

from txcollections.models import (Collection, CollectionRelease as Release)
from txcollections.forms import *


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


# A set of limited-access generic views to re-use
# TODO: Move this in transifex-core
@login_required
def limited_create_object(*args, **kwargs):
    return create_update.create_object(*args, **kwargs)

@login_required
def limited_update_object(*args, **kwargs):
    return create_update.update_object(*args, **kwargs)

@login_required
def limited_delete_object(*args, **kwargs):
    return create_update.delete_object(*args, **kwargs)


# Collections

def collection_delete(*args, **kwargs):
    kwargs['post_delete_redirect'] = reverse('collection_list', args=[kwargs['slug']])
    return limited_delete_object(*args, **kwargs)


# Releases

def release_delete(*args, **kwargs):
    kwargs['post_delete_redirect'] = reverse('collection_detail', args=[kwargs['slug']])
    return limited_delete_object(*args, **kwargs)


def release_detail(request, slug, release_slug, *args, **kwargs):
    collection = get_object_or_404(Collection, slug__exact=slug)
    release = get_object_or_404(Release, slug__exact=release_slug,
                                collection=collection)
    components = release.components.order_by('project', 'name')
    return list_detail.object_detail(
        request,
        queryset = Release.objects.all(),
        slug=release_slug,
        extra_context = {'collection': collection, 'components': components},
        *args, **kwargs)


@login_required
def release_create_update(request, slug, release_slug=None, *args, **kwargs):
    collection = get_object_or_404(Collection, slug__exact=slug)
    if release_slug:
        release = get_object_or_404(Release, slug__iexact=release_slug,
                                    collection=collection)
    else:
        release = None
    if request.method == 'POST':
        release_form = ReleaseForm(collection, request.POST, instance=release)
        if release_form.is_valid():
            release = release_form.save()
            return HttpResponseRedirect(
                reverse('collection_release_detail',
#                        kwargs = {'slug': slug,
#                                  'release_slug': release.slug,}))
                         args=[slug, release.slug]))
    else:
        release_form = ReleaseForm(collection, instance=release)
    return render_to_response('txcollections/release_form.html', {
        'form': release_form,
        'collection': collection,
        'release': release,
    }, context_instance=RequestContext(request))
