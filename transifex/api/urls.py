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
project_handler = Resource(ProjectHandler)
jsonstring_handler = Resource(JSONStringHandler)
trstring_handler = Resource(TResourceStringHandler)
pjstring_handler = Resource(ProjectStringHandler)

urlpatterns = patterns('',
    url(
        r'^languages/$',
        language_handler,
        name='api.languages',
    ), url(
        r'^project/$',
        project_handler,
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/$',
        project_handler,
        name='api_project',
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/pull_strings/$',
        pjstring_handler
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resources/$',
        tresource_handler
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/$',
        tresource_handler,
        name='api_resource'
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/push_strings/$',
        jsonstring_handler,
        name='jsonstring_resource_push'
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/pull_strings/$',
        trstring_handler,
        name='jsonstring_resource_pullall'
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/pull_strings/(?P<target_lang_code>[-\w]+)/$',
        jsonstring_handler,
        name='jsonstring_resource_pullfrom'
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
        r'^storage/(?P<uuid>[-\w]+)/$',
        storage_handler,
        name='api.storage.file'
    ),
)
