from django.conf.urls.defaults import *
from django.contrib import admin
from tagging.views import tagged_object_list

from txcollections.views import * 
from txcollections.feeds import (LatestCollections, CollectionFeed)

admin.autodiscover()

collection_list = {
    'queryset': Collection.objects.all(),
    'template_object_name': 'collection',
}

feeds = {
    'latest': LatestCollections,
    'collection': CollectionFeed,
}

# Collections

urlpatterns = patterns('django.views.generic',
    url(
        regex = '^add/$',
        view = collection_create,
        name = 'collection_create',
        kwargs = {'model': Collection}),
    url(
        regex = '^(?P<slug>[-\w]+)/edit/$',
        view = collection_update,
        name = 'collection_edit',
        kwargs = {'model': Collection,
                  'template_object_name': 'collection',}),
    url(
        regex = '^(?P<slug>[-\w]+)/delete/$',
        view = collection_delete,
        name = 'collection_delete',
        kwargs = {'model': Collection,
                  'template_object_name': 'collection',}),
    url(
        regex = '^(?P<slug>[-\w]+)/$',
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

urlpatterns += patterns('',
    url(
        regex = r'^feed/$',
        view = 'txcollections.views.slug_feed',
        name = 'collection_latest_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'latest'}),
    url(
        regex = r'^(?P<param>[-\w]+)/feed/$',
        view = 'txcollections.views.slug_feed',
        name = 'collection_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'collection'}),
)
