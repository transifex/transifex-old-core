from django.conf.urls.defaults import *
from tagging.views import tagged_object_list

from txcollections.views import * 
from txcollections.feeds import (LatestCollections, CollectionFeed,
                                 ReleaseLanguagesFeed)
from txcollections.models import Collection

collection_list = {
    'queryset': Collection.objects.all(),
    'template_object_name': 'collection',
}

feeds = {
    'latest': LatestCollections,
    'collection': CollectionFeed,
    'release_languages': ReleaseLanguagesFeed,
}

# Collections

urlpatterns = patterns('django.views.generic',
    url(
        regex = '^add/$',
        view = limited_create_object,
        name = 'collection_create',
        kwargs = {'model': Collection}),
    url(
        regex = '^c/(?P<slug>[-\w]+)/edit/$',
        view = limited_update_object,
        name = 'collection_edit',
        kwargs = {'model': Collection,
                  'template_object_name': 'collection',}),
    url(
        regex = '^c/(?P<slug>[-\w]+)/delete/$',
        view = collection_delete,
        name = 'collection_delete',
        kwargs = {'model': Collection,
                  'template_object_name': 'collection',}),
    url(
        regex = '^c/(?P<slug>[-\w]+)/$',
        view = 'list_detail.object_detail',
        name = 'collection_detail',
        kwargs = collection_list,),
    url (
        regex = '^$',
        view = 'list_detail.object_list',
        kwargs = collection_list,
        name = 'collection_list'),
    url(
        r'^tag/(?P<tag>[^/]+)/$',
        tagged_object_list,
        dict(queryset_or_model=Collection, allow_empty=True,
             template_object_name='collection'),
        name='collection_tag_list'),
)

## More

#TODO: Temporary until we import view from a common place
SLUG_FEED = 'txcollections.views.slug_feed'
urlpatterns += patterns('',
    url(
        # FIXME: This doesn't seem to work with a trailing / ?!
        regex = r'^feed$',
        view = SLUG_FEED,
        name = 'collection_latest_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'latest'}),
    url(
        regex = r'^c/(?P<param>[-\w]+)/releases/feed/$',
        view = SLUG_FEED,
        name = 'collection_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'collection'}),
    url(
        regex = '^c/(?P<collection_slug>[-\w]+)/r/(?P<release_slug>[-\w]+)/feed/$',
        view = release_languages_feed,
        name = 'release_languages_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'release_languages'}),
)

# Releases

urlpatterns += patterns('',
    url(
        regex = '^c/(?P<slug>[-\w]+)/add-release/$',
        view = release_create_update,
        name = 'collection_release_create',
        kwargs = {'model': Release,}),
    url(
        regex = '^c/(?P<slug>[-\w]+)/r/(?P<release_slug>[-\w]+)/edit/$',
        view = release_create_update,
        name = 'collection_release_edit',
        kwargs = {'model': Release,
                  'template_object_name': 'release'}),
    url(
        regex = '^c/(?P<collection_slug>[-\w]+)/r/(?P<release_slug>[-\w]+)/delete/$',
        view = collection_release_delete,
        name = 'collection_release_delete',),

    url (
        regex = '^c/(?P<slug>[-\w]+)/release-added/$',
        view = 'django.views.generic.list_detail.object_detail',
        name = 'collection_release_created',
        kwargs = {'object_list': collection_list,
                  'message': 'Component added.' },),
    url(
        regex = '^c/(?P<slug>[-\w]+)/r/(?P<release_slug>[-\w]+)/$',
        view = release_detail,
        name = 'collection_release_detail',
        kwargs = {'template_object_name': 'release',
                  'template_name': 'txcollections/release_detail.html',}),
)
