from django.conf.urls.defaults import *
from django.contrib import admin
from models import Language
from feeds import AllLanguages
from views import language_detail, slug_feed

admin.autodiscover()

feeds = {
    'all': AllLanguages,
}

urlpatterns = patterns('',
    url(
        regex = r'^feed/$',
        view = 'languages.views.slug_feed',
        name = 'languages_latest_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'all'}),
)


urlpatterns += patterns('django.views.generic',
    url (
        name = 'language_list',
        regex = '^$',
        view = 'list_detail.object_list',
        kwargs = {"template_object_name" : "language",
                  'queryset': Language.objects.all()}
    ),
    url(
        name = 'language_detail',
        regex = '^(?P<slug>[-_@\w]+)/$',
        view = language_detail,
        kwargs = {'slug_field': 'code',
                  "template_object_name" : "language",
                  'queryset': Language.objects.all()}
    ),
)