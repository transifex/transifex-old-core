from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
import authority

from txcommon.forms import EditProfileForm
from txcommon.feeds import UserFeed

# Overriding 500 error handler
handler500 = 'views.server_error'

admin.autodiscover()
authority.autodiscover()

panel_url = getattr(settings,'DJANGO_ADMIN_PANEL_URL', 'admin')

urlpatterns = patterns('',)

if settings.ENABLE_ADDONS:
    urlpatterns += patterns('', (r'', include('django_addons.urls')))

PROJECTS_URL = '^projects/'

urlpatterns += patterns('',
    url(r'^$', 'txcommon.views.index', name='transifex.home'),
    url(PROJECTS_URL, include('projects.urls')),
    url(r'^search/$', 'txcommon.views.search', name='search'),
    url(r'^%s/doc/' % panel_url, include('django.contrib.admindocs.urls')),
    url(r'^%s/' % panel_url, include(admin.site.urls)),
    url(r'^languages/', include('languages.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^ajax/', include('ajax_select.urls')),
    url(r'^ajax/', include('resources.urls.ajax')),
    url(r'^api/', include('api.urls')),
    url(r'^tagging_autocomplete/', include('tagging_autocomplete.urls')),
)

if settings.ENABLE_CONTACT_FORM:
    urlpatterns += patterns('',
        url(r'^contact/', include('contact_form.urls'), name='contact'),
    )

urlpatterns += patterns('',
        url(r'^accounts/profile/(?P<username>.+)/feed/$', UserFeed(), name='user_feed')
)

if settings.ENABLE_SIMPLEAUTH:
    urlpatterns += patterns('',
        url(r'^accounts/', include('simpleauth.urls')),)
else:
    urlpatterns += patterns('',
        # Custom EditProfileForm
        url(regex   =   r'^accounts/(?P<username>(?!signout|signup|signin)[\.\w]+)/$',
            view    =   'userena.views.profile_edit',
            kwargs  =   {'edit_profile_form': EditProfileForm},
            name    =   'userena_profile_edit'),

        url(regex   =   r'^accounts/',
            view    =   include('userena.urls')),

        url(regex   =   r'^accounts/profile/(?P<username>.+)/$',
            view    =   'txcommon.views.profile_public',
            name    =   'profile_public'),
    )

if settings.USE_SOCIAL_LOGIN:
    urlpatterns += patterns('',
        url(r'^accounts/', include('social_auth.urls')),
        url(r'^accounts/(?P<username>(?!signout|signup|signin)[\.\w]+)/social/$',
            view='txcommon.views.profile_social_settings', name='profile_social_settings')
    )

if settings.ENABLE_NOTICES:
    urlpatterns += patterns('',
        (r'^notices/', include('notification.urls')),
        url(r'^accounts/nudge/(?P<username>.+)/$', 'txcommon.views.user_nudge', name='user_nudge'),
    )

if settings.SERVE_MEDIA:
    urlpatterns += patterns('',
        url(r'^site_media/media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )
