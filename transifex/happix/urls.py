# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from happix.views import *


urlpatterns = patterns('',
    # Search strings
    url(r'^search/$', search_translation, name='search_translation'),

    # Resources
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/$', resource_detail, name='resource_detail'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/edit$', resource_edit, name='resource_edit'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/delete$', resource_delete, name='resource_delete'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/delete_all/$', resource_translations_delete, name='resource_translations_delete'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<target_lang_code>[-\w]+)/actions/$', resource_actions, name='resource_actions'),

    # Project resources list
    url(r'^project/(?P<project_slug>[-\w]+)/resources/(?P<offset>\d+)$', project_resources, name='project_resources'),
    url(r'^project/(?P<project_slug>[-\w]+)/resources/(?P<offset>\d+)/more/$', project_resources, kwargs={'more':True}, name='project_resources_more'),

    # Overrides for N/A views
    url(r'^project/(?P<project_slug>[-\w]+)/(?P<lang_code>[-\w]+)/$', not_available, name='translate'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/$', not_available, name='translate'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/view/$', not_available, name='view_strings'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/download/$', get_translation_file, name='download_translation'),

)
