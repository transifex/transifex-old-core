import os
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import create_update, list_detail
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import feed

from translations.models import POFile
from txcollections.models import (Collection, CollectionRelease as Release)
from txcollections.forms import *
from txcommon.decorators import perm_required_with_403

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

def release_languages_feed(request, collection_slug, release_slug,
                           slug=None, param='', feed_dict=None,):
    param = '%s/%s' % (collection_slug, release_slug)
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)

# A set of limited-access generic views to re-use
# TODO: Move this in transifex-core
@login_required
@perm_required_with_403('txcollections.add_collection')
def limited_create_object(*args, **kwargs):
    return create_update.create_object(*args, **kwargs)

@login_required
@perm_required_with_403('txcollections.change_collection')
def limited_update_object(*args, **kwargs):
    return create_update.update_object(*args, **kwargs)

# Generic function to delete objects
def limited_delete_object(*args, **kwargs):
    return create_update.delete_object(*args, **kwargs)


# Collections
@login_required
@perm_required_with_403('txcollections.delete_collection')
def collection_delete(*args, **kwargs):
    kwargs['post_delete_redirect'] = reverse('collection_list')
    return limited_delete_object(*args, **kwargs)


# Releases

@login_required
@perm_required_with_403('txcollections.add_collectionrelease')
@perm_required_with_403('txcollections.change_collectionrelease')
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


def release_detail(request, slug, release_slug, *args, **kwargs):
    collection = get_object_or_404(Collection, slug__exact=slug)
    release = get_object_or_404(Release, slug__exact=release_slug,
                                collection=collection)
    pofile_list = POFile.objects.by_release_total(release)
    return list_detail.object_detail(
        request,
        queryset = Release.objects.all(),
        object_id = release.id,
        extra_context = {'pofile_list': pofile_list,
                         'release': release,
                         'collection': collection},
        *args, **kwargs)

@login_required
@perm_required_with_403('txcollections.delete_collectionrelease')
def collection_release_delete(request, collection_slug, release_slug):
    release = get_object_or_404(Release, slug=release_slug,
                                  collection__slug=collection_slug)
    if request.method == 'POST':
        import copy
        release_ = copy.copy(release)
        release.delete()
        request.user.message_set.create(
            message=_("The %s was deleted.") % release.name)

        # ActionLog & Notification
        #nt = 'collection_release_deleted'
        #context = {'component': component_}
        #action_logging(request.user, [component_.project], nt, context=context)
        #if settings.ENABLE_NOTICES:
            #txnotification.send_observation_notices_for(component_.project,
                                #signal=nt, extra_context=context)

        return HttpResponseRedirect(reverse('collection_detail', 
                                     args=(collection_slug,)))
    else:
        return render_to_response('txcollections/release_confirm_delete.html',
                                  {'release': release,},
                                  context_instance=RequestContext(request))

