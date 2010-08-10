# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from views import project_toggle_watch, resource_translation_toggle_watch

urlpatterns = patterns('',
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/toggle_watch/$',
        view = project_toggle_watch,
        name = 'project_toggle_watch',),
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/toggle_watch/l/(?P<language_code>[\-_@\w]+)$',
        view = resource_translation_toggle_watch,
        name = 'resource_translation_toggle_watch',),
)
