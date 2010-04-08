# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from happix.views import search_translation


urlpatterns = patterns('',
    url(r'^search/$', search_translation, name='search_translation'),
)
