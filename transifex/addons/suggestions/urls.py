# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from views import *

from resources.urls import RESOURCE_LANG_URL

#FIXME: Move this to resource if we agree.
ENTITY_URL = '^entities/(?P<entity_id>\d+)/'
SUGGESTIONS_URL = ENTITY_URL + 'lang/(?P<lang_code>[-\w]+)/suggestions/'

urlpatterns = patterns('',
    url(SUGGESTIONS_URL+'snippet/$',
        entity_suggestions_snippet, name='entity_suggestions_snippet'),
    url(SUGGESTIONS_URL+'create/$',
        entity_suggestion_create, name='entity_suggestion_create'),
    url(SUGGESTIONS_URL+'(?P<suggestion_id>\d+)/vote/1/$',
        entity_suggestion_vote, {'direction': 'up'},
        name='entity_suggestion_vote_up',),
    url(SUGGESTIONS_URL+'(?P<suggestion_id>\d+)/vote/-1/$',
        entity_suggestion_vote, {'direction': 'down'},
        name='entity_suggestion_vote_down',),
)

