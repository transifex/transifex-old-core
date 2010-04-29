# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from views import project_toggle_watch, component_toggle_watch

urlpatterns = patterns('',
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/toggle_watch/$',
        view = project_toggle_watch,
        name = 'project_toggle_watch',),
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/toggle_watch/pofile/(?P<filename>(.*))$',
        view = component_toggle_watch,
        name = 'component_toggle_watch',),
)
