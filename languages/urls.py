from django.conf.urls.defaults import *
from django.contrib import admin
from models import Language
from feeds import AllLanguages
from views import language_detail

admin.autodiscover()

feeds = {
    'all': AllLanguages,
}

# These urlconfs are being mounted directly at /, so make sure they don't
# conflict with anything else in the main urls.py
urlpatterns = patterns('',
    url(
        name = 'language_feed',
        regex = r'^feeds/(?P<url>[-\w]+)/$',
        view = 'django.contrib.syndication.views.feed',
        kwargs = {'feed_dict': feeds}),
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
        regex = '^(?P<slug>[-\w]+)/$',
        view = language_detail,
        kwargs = {'slug_field': 'code',
                  "template_object_name" : "language",
                  'queryset': Language.objects.all()}
    ),
)