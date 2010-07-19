# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from views import component_file_unlock, component_file_lock

urlpatterns = patterns('',
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/unlock/(?P<filename>(.*))/$',
        view = component_file_unlock,
        name = 'component_file_unlock',),
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/lock/(?P<filename>(.*))/$',
        view = component_file_lock,
        name = 'component_file_lock',),
)
