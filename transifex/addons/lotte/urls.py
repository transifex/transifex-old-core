# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from lotte.views import *



urlpatterns = patterns('',
    # Server side lotte
    url(r'^resources/project/(?P<project_slug>[-\w]+)/(?P<lang_code>[-\w]+)/$', translate, name='translate'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/(?P<lang_code>[-\w]+)/details/$', get_details, name='get_details'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/(?P<lang_code>[-\w]+)/stringset/$', stringset_handling, name='stringset_handling'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/(?P<lang_code>[-\w]+)/push/$', push_translation, name='push_translation'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/(?P<lang_code>[-\w]+)/delete/$', delete_translation, name='delete_translation'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/(?P<lang_code>[-\w]+)/exit/$', exit, name='exit_lotte'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<lang_code>[-\w]+)/$', translate, name='translate'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<lang_code>[-\w]+)/details/$', get_details, name='get_details'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<lang_code>[-\w]+)/view/$', view_strings, name='view_strings'),
#    url(r'^resources/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<source_lang_code>[-\w]+)/clone/(?P<target_lang_code>[-\w]+)/$', clone_language, name='clone_translate'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<lang_code>[-\w]+)/stringset/$', stringset_handling, name='stringset_handling'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<lang_code>[-\w]+)/push/$', push_translation, name='push_translation'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<lang_code>[-\w]+)/delete/$', delete_translation, name='delete_translation'),
    url(r'^resources/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/l/(?P<lang_code>[-\w]+)/exit/$', exit, name='exit_lotte'),
)
