# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from views import resource_language_lock, resource_language_unlock

urlpatterns = patterns('',
    url(
        regex = r'^projects/p/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<language_code>[\-_@\w]+)/lock/$',
        view = resource_language_lock,
        name = 'resource_language_lock',),
    url(
        regex = r'^projects/p/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<language_code>[\-_@\w]+)/unlock/$',
        view = resource_language_unlock,
        name = 'resource_language_unlock',),
    # We exploit the create_update to do the extend lock action with the same view as lock creation.
    url(
        regex = r'^projects/p/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<language_code>[\-_@\w]+)/extend/$',
        view = resource_language_lock,
        name = 'resource_language_extend',),
)

