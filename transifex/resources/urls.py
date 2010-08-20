# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from projects.urls import PROJECTS_URL, PROJECT_URL, PROJECT_URL_PARTIAL
from resources.views import *

# General URLs:
urlpatterns = patterns('',
    # Search strings
    url(r'^search/$', search_translation, name='search_translation'),

    # Project resources list
    url(PROJECT_URL+r'resources/(?P<offset>\d+)$',
        project_resources, name='project_resources'),
    url(PROJECT_URL+r'resources/(?P<offset>\d+)/more/$',
        project_resources, name='project_resources_more', kwargs={'more':True}),
)


# Resource-specific URLs:
# URL relative to the projects app (no '/projects' prefix)
RESOURCE_URL_PARTIAL = PROJECT_URL_PARTIAL + r'resource/(?P<resource_slug>[-\w]+)/'
# URL which should be used from other addons (full with prefix)
RESOURCE_URL = PROJECTS_URL + RESOURCE_URL_PARTIAL

# URL relative to the projects app (no '/projects' prefix)
RESOURCE_LANG_URL_PARTIAL = RESOURCE_URL_PARTIAL + r'l/(?P<lang_code>[-_@\w]+)/'
# URL which should be used from other addons (full with prefix)
RESOURCE_LANG_URL = PROJECTS_URL + RESOURCE_LANG_URL_PARTIAL

# Use _PARTIAL since this whole file is included from inside projects/urls.py.
urlpatterns += patterns('',
    # Resources
    url(RESOURCE_URL_PARTIAL+r'$', resource_detail, name='resource_detail'),
    url(RESOURCE_URL_PARTIAL+r'edit$', resource_edit, name='resource_edit'),
    url(RESOURCE_URL_PARTIAL+r'delete$', resource_delete, name='resource_delete'),
    # Resources-Lang
    url(RESOURCE_LANG_URL_PARTIAL+'delete_all/$',
        resource_translations_delete, name='resource_translations_delete'),
    url(RESOURCE_URL_PARTIAL+r'l/(?P<target_lang_code>[-_@\w]+)/actions/$',
        resource_actions, name='resource_actions'),
    url(RESOURCE_LANG_URL_PARTIAL+'download/$',
        get_translation_file, name='download_translation'),
)
