# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.decorators.cache import never_cache
from piston.resource import Resource
#from piston.authentication import OAuthAuthentication
from transifex.api.authentication import CustomHttpBasicAuthentication

#TODO: Implement full support for OAUTH and refactor URLs!
#auth = OAuthAuthentication(realm='Transifex API')

from transifex.languages.api import LanguageHandler
from transifex.projects.api import ProjectHandler, ProjectResourceHandler
from transifex.resources.api import ResourceHandler, FileHandler, StatsHandler, \
        TranslationHandler
from transifex.storage.api import StorageHandler
from transifex.releases.api import ReleaseHandler

auth = CustomHttpBasicAuthentication(realm='Transifex API')

resource_handler = Resource(ResourceHandler, authentication=auth)
release_handler = Resource(ReleaseHandler, authentication=auth)
storage_handler = Resource(StorageHandler, authentication=auth)
project_handler = Resource(ProjectHandler, authentication=auth)
projectresource_handler = Resource(ProjectResourceHandler, authentication=auth)
translationfile_handler = Resource(FileHandler, authentication=auth)
stats_handler = Resource(StatsHandler, authentication=auth)
translation_handler = Resource(TranslationHandler, authentication=auth)

urlpatterns = patterns('',
    url(
        r'^languages/$',
        Resource(LanguageHandler),
        {'api_version': 1},
        name='api.languages',
    ), url(
        r'^projects/$',
        project_handler,
        {'api_version': 1},
        name='api_projects',
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/$',
        never_cache(project_handler),
        {'api_version': 1},
        name='api_project',
     ), url(
        r'^project/(?P<project_slug>[-\w]+)/files/$',
        projectresource_handler,
        {'api_version': 1},
        name='api_project_files',
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resources/$',
        never_cache(resource_handler),
        {'api_version': 1},
        name="api_resources",
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/$',
        never_cache(resource_handler),
        {'api_version': 1},
        name='api_resource',
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/release/(?P<release_slug>[-\w]+)/$',
        never_cache(release_handler),
        {'api_version': 1},
        name='api_release',
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/stats/$',
        never_cache(stats_handler),
        {'api_version': 1},
        name='api_resource_stats',
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/stats/(?P<lang_code>[\-_@\w]+)/$',
        never_cache(stats_handler),
        {'api_version': 1},
        name='api_resource_stats',
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<language_code>[\-_@\w]+)/$',
        never_cache(projectresource_handler),
        {'api_version': 1},
        name='api_resource_storage',
    ), url(
        r'^project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<language_code>[\-_@\w]+)/file/$',
        never_cache(translationfile_handler),
        {'api_version': 1},
        name='api_translation_file',
    ), url(
        r'^storage/$',
        storage_handler,
        {'api_version': 1},
        name='api.storage',
    ), url(
        r'^storage/(?P<uuid>[-\w]+)/$',
        storage_handler,
        {'api_version': 1},
        name='api.storage.file',
    ), url(
        r'^2/projects/$',
        never_cache(project_handler),
        {'api_version': 2},
        name='apiv2_projects',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/$',
        never_cache(project_handler),
        {'api_version': 2},
        name='apiv2_project',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resources/$',
        never_cache(resource_handler),
        {'api_version': 2},
        name='apiv2_resources',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/$',
        never_cache(resource_handler),
        {'api_version': 2},
        name='apiv2_resource',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/content/$',
        never_cache(translation_handler),
        {'api_version': 2, 'lang_code': 'source'},
        name='apiv2_translations',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/translation/(?P<lang_code>[\-_@\w]+)/$',
        never_cache(translation_handler),
        {'api_version': 2},
        name='apiv2_translation',
    ), url(
        r'^1/languages/$',
        Resource(LanguageHandler),
        {'api_version': 1},
        name='api.languages',
    ), url(
        r'^1/projects/$',
        project_handler,
        {'api_version': 1},
        name='api_projects',
    ), url(
        r'^1/project/(?P<project_slug>[-\w]+)/$',
        never_cache(project_handler),
        {'api_version': 1},
        name='api_project',
     ), url(
        r'^1/project/(?P<project_slug>[-\w]+)/files/$',
        projectresource_handler,
        {'api_version': 1},
        name='api_project_files',
    ), url(
        r'^1/project/(?P<project_slug>[-\w]+)/resources/$',
        never_cache(resource_handler),
        {'api_version': 1},
        name="api_resources",
    ), url(
        r'^1/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/$',
        never_cache(resource_handler),
        {'api_version': 1},
        name='api_resource',
    ), url(
        r'^1/project/(?P<project_slug>[-\w]+)/release/(?P<release_slug>[-\w]+)/$',
        never_cache(release_handler),
        {'api_version': 1},
        name='api_release',
    ), url(
        r'^1/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/stats/$',
        never_cache(stats_handler),
        {'api_version': 1},
        name='api_resource_stats',
    ), url(
        r'^1/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/stats/(?P<lang_code>[\-_@\w]+)/$',
        never_cache(stats_handler),
        {'api_version': 1},
        name='api_resource_stats',
    ), url(
        r'^1/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<language_code>[\-_@\w]+)/$',
        never_cache(projectresource_handler),
        {'api_version': 1},
        name='api_resource_storage',
    ), url(
        r'^1/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<language_code>[\-_@\w]+)/file/$',
        never_cache(translationfile_handler),
        {'api_version': 1},
        name='api_translation_file',
    ), url(
        r'^1/storage/$',
        storage_handler,
        {'api_version': 1},
        name='api.storage',
    ), url(
        r'^1/storage/(?P<uuid>[-\w]+)/$',
        storage_handler,
        {'api_version': 1},
        name='api.storage.file',
    ),
)
