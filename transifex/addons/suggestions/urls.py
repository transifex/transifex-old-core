# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from views import *

from resources.urls import RESOURCE_LANG_URL

SUGGESTIONS_URL = RESOURCE_LANG_URL+'suggestions/'

urlpatterns = patterns('',
    # Server side lotte
    url(SUGGESTIONS_URL+'$', get_suggestions, name='get_suggestions'),
    url(SUGGESTIONS_URL+'create/$',
        suggestion_create, name='suggestion_create'),
    url(SUGGESTIONS_URL+'vote/$',
        suggestion_vote_updown, name='suggestion_vote_updown'),
)
