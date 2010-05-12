# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import OAuthAuthentication

from api.handlers import *

#TODO: Implement full support for OAUTH and refactor URLs!
#auth = OAuthAuthentication(realm='Happix API')
language_handler = Resource(LanguageHandler)
tresource_handler = Resource(TResourceHandler)
strings_handler = Resource(StringHandler)
storage_handler = Resource(StorageHandler)

urlpatterns = patterns('',
    url(
        r'^languages/$',
        language_handler,
        name='api.languages',
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resources/$', 
        tresource_handler
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/$',
        tresource_handler,
        name='api_resource'
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/(?P<target_lang_code>[-\w]+)/$',
        strings_handler,
        name='api_resource_translation'
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/(?P<target_lang_code>[-\w]+)/(?P<source_lang_code>[-\w]+)/$',
        strings_handler,
        name='api_resource_translation_from'

    ), url(
        r'^storage/$',
        storage_handler,
        name='api.storage'
    ), url(
        r'^storage/(?P<storage_uuid>[-\w]+)/$',
        storage_handler,
        name='api.storage.file'
    ),
)
