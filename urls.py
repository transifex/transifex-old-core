from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin


urlpatterns = patterns('',
    url(r'^$', 'django.views.generic.simple.direct_to_template',
        {'template': 'index.html'}, name='home'),
    url(r'^projects/', include('projects.urls')),
    url(r'^search/$', 'transifex.views.search', name='search'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/(.*)', admin.site.root),
    url(r'^contact/', include('contact_form.urls'), name='contact'),
    url(r'^account/', include('django_authopenid.urls')),
    url(r'^$', 'django.views.generic.simple.direct_to_template',
        {'template': 'index.html'}, name='login'),
)

if settings.STATIC_SERVE:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
