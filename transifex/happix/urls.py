# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from happix.views import * 


urlpatterns = patterns('',
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/$', view_translation_resource, name='project.resource'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/$', view_translation, name='translation'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/create_language/(?P<target_lang_code>[-\w]+)/$', start_new_translation, name='new_translation'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/(?P<source_lang_code>[-\w]+)/clone/(?P<target_lang_code>[-\w]+)/$', clone_translation, name='clone_translation'),
#    url(r'^search/$', search_translation, name='search_translation'),

)
