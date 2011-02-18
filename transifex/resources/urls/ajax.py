# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from transifex.resources.urls import RESOURCE_URL_PARTIAL
from transifex.resources.views import resource_actions

urlpatterns = patterns('',
    url(RESOURCE_URL_PARTIAL + r'l/(?P<target_lang_code>[\-_@\w]+)/actions/$',
        resource_actions, name='resource_actions'),
)
