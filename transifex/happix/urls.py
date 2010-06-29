# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from happix.views import * 


urlpatterns = patterns('',
#    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/$', view_translation, name='translation'),
#    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/create_language/(?P<target_lang_code>[-\w]+)/$', start_new_translation, name='new_translation'),

    # Server side lotte
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/$', translate, name='translate'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/details/$', get_details, name='get_details'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/view/$', view_strings, name='view_strings'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<source_lang_code>[-\w]+)/clone/(?P<target_lang_code>[-\w]+)/$', clone_language, name='clone_translate'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/stringset/$', stringset_handling, name='stringset_handling'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/push/$', push_translation, name='push_translation'),
    
#    url(r'^search/$', search_translation, name='search_translation'),

    # Resources
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/$', resource_detail, name='resource_detail'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/edit$', resource_edit, name='resource_edit'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/delete$', resource_delete, name='resource_delete'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/delete/$', resource_translations_delete, name='resource_translations_delete'),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/actions/(?P<target_lang_code>[-\w]+)/$', resource_actions, name='resource_actions'),

    # Project resources list
    url(r'^project/(?P<project_slug>[-\w]+)/resources/(?P<offset>\d+)$', project_resources, name='project_resources'),
    url(r'^project/(?P<project_slug>[-\w]+)/resources/(?P<offset>\d+)/more/$', project_resources, kwargs={'more':True}, name='project_resources_more'),
)
