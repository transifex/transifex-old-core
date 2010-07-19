# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from piston.resource import Resource
#from piston.authentication import OAuthAuthentication
from api.authentication import CustomHttpBasicAuthentication



#TODO: Implement full support for OAUTH and refactor URLs!
#auth = OAuthAuthentication(realm='Happix API')

from languages.api import LanguageHandler
from projects.api import ProjectHandler, ProjectResourceHandler
from storage.api import StorageHandler
from happix.api import (ResourceHandler, StringHandler)

auth = CustomHttpBasicAuthentication(realm='Happix API')

resource_handler = Resource(ResourceHandler, authentication=auth)
storage_handler = Resource(StorageHandler, authentication=auth)
project_handler = Resource(ProjectHandler, authentication=auth)
projectresource_handler = Resource(ProjectResourceHandler, authentication=auth)
string_handler = Resource(StringHandler, authentication=auth)
#projectstring_handler = Resource(ProjectStringHandler)




urlpatterns = patterns('',
    url(
        r'^languages/$',
        Resource(LanguageHandler),
        name='api.languages',
    ), url(
        r'^projects/$',
        project_handler,
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/$',
        project_handler,
        name='api_project',
     ), url(
        r'^project/(?P<project_slug>[-\w]+)/files/$',
        projectresource_handler,
        name='api_project',
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/strings/$',
        string_handler
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/strings/(?P<target_lang_code>[-\w]+)/$',
        string_handler
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resources/$',
        resource_handler
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/$',
        resource_handler,
        name='api_resource'
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/string/$',
        string_handler,
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/strings/$',
        string_handler,
        name='string_resource_push'
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/strings/(?P<target_lang_code>[-\w]+)/$',
        string_handler,
        name='string_resource_pullfrom'
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<language_code>[-_@\w]+)/$',
        projectresource_handler,
        name='api_resource_translation_storage'
#    ), url(
#        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<target_lang_code>[-\w]+)/(?P<source_lang_code>[-\w]+)/$',
#        strings_handler,
#        name='api_resource_translation_from'
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
