from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
import authority

admin.autodiscover()
authority.autodiscover()

urlpatterns = patterns('',
    #url(r'^$', 'django.views.generic.simple.direct_to_template',
    #    {'template': 'index.html'}, name='home'),
    url(r'^$', 'txcommon.views.index', name='transifex.home'),
    url(r'^projects/', include('projects.urls')),
    url(r'^collections/', include('txcollections.urls')),
    url(r'^search/$', 'txcommon.views.search', name='search'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/(.*)', admin.site.root),
    url(r'^contact/', include('contact_form.urls'), name='contact'),
    url(r'^languages/', include('languages.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
)

if settings.ENABLE_SIMPLEAUTH:
    urlpatterns += patterns('',
        url(r'^accounts/', include('simpleauth.urls')),)
else:
    urlpatterns += patterns('',
        url(r'^accounts/', include('userprofile.urls')),
    )

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )

if settings.ENABLE_NOTICES:
    urlpatterns += patterns('',
        (r'^notices/', include('notification.urls')),
    )
