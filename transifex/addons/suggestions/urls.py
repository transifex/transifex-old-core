# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from views import *



urlpatterns = patterns('',
    # Server side lotte
    url(r'^happix/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/suggestions/$', get_suggestions, name='get_suggestions'),
    url(r'^happix/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/suggestions/create/$', suggestion_create, name='suggestion_create'),
    url(r'^happix/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/(?P<lang_code>[-\w]+)/suggestions/vote/$', suggestion_vote_updown, name='suggestion_vote_updown'),
)
