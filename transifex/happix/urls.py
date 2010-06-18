# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from happix.views import * 


urlpatterns = patterns('',
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/$', view_translation_resource, name='project.resource'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/$', view_translation, name='translation'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/create_language/(?P<target_lang_code>[-\w]+)/$', start_new_translation, name='new_translation'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<source_lang_code>[-\w]+)/clone/(?P<target_lang_code>[-\w]+)/$', clone_translation, name='clone_translation'),
#    url(r'^search/$', search_translation, name='search_translation'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/edit$', edit_translation_resource, name='resource_edit'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/delete$', delete_translation_resource, name='resource_delete'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/actions/(?P<target_lang_code>[-\w]+)/$', resource_actions, name='resource_actions'),

    url(r'^project/(?P<project_slug>[-\w]+)/resources/(?P<offset>\d+)$', project_resources, name='project_resources'),
    url(r'^project/(?P<project_slug>[-\w]+)/resources/(?P<offset>\d+)/more/$', project_resources, kwargs={'more':True}, name='project_resources_more'),
)
