# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from happix.views import search_translation, \
    view_projects, view_project, view_translation_resource, view_stringset


urlpatterns = patterns('',
    url(r'^projects/$', view_projects, name='_projects'),
    url(r'^project/(?P<project_slug>[-\w]+)/$', view_project, name='_project'),
    url(r'^project/(?P<project_slug>[-\w]+)/(?P<tresource_slug>[-\w]+)/$', view_translation_resource, name='_project_resource'),

    url(r'^project/(?P<project_slug>[-\w]+)/(?P<tresource_slug>[-\w]+)/(?P<to_lang>[-\w]+)/$', view_translation_resource, name='_project_resource'),

    url(r'^project/(?P<project_slug>[-\w]+)/(?P<tresource_slug>[-\w]+)/stringset(?P<stringset_path>(.*))/$', view_stringset, name='_stringset'),

    url(r'^search/$', search_translation, name='search_translation'),

)
