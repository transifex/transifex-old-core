# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from happix.views import view_translation_resource, view_translation


urlpatterns = patterns('',
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/$', view_translation_resource, name='project.resource'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/$', view_translation, name='translation'),
#    url(r'^search/$', search_translation, name='search_translation'),

)
