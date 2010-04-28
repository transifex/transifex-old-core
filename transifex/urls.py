from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
import authority

admin.autodiscover()
authority.autodiscover()

panel_url = getattr(settings,'DJANGO_ADMIN_PANEL_URL', 'admin')

urlpatterns = patterns('',
    #url(r'^$', 'django.views.generic.simple.direct_to_template',
    #    {'template': 'index.html'}, name='home'),
    url(r'^$', 'txcommon.views.index', name='transifex.home'),
    url(r'^projects/', include('projects.urls')),
    url(r'^reviews/', include('reviews.urls')),
    url(r'^search/$', 'txcommon.views.search', name='search'),
    url(r'^%s/doc/' % panel_url, include('django.contrib.admindocs.urls')),
    url(r'^%s/' % panel_url, include(admin.site.urls)),
    url(r'^languages/', include('languages.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^ajax/', include('ajax_select.urls')),
    url(r'^accounts/timeline/$', 'txcommon.views.user_timeline', name='user_timeline'),
    url(r'^threadedcomments/', include('threadedcomments.urls')),
)

if settings.ENABLE_CONTACT_FORM:
    urlpatterns += patterns('',
        url(r'^contact/', include('contact_form.urls'), name='contact'),
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
        url(r'^accounts/nudge/(?P<username>.+)/$', 'txcommon.views.user_nudge', name='user_nudge'),
    )
