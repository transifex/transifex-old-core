"""
Simple URLConf for Django user authentication (no registration).
"""

from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib.auth import views as auth_views
from django.utils.translation import ugettext as _
from simpleauth.views import login, logout, account_settings

urlpatterns = patterns('',
    url(r'^signin/$', login, name='user_signin'),
    url(r'^signout/$', logout, name='user_signout'),
    url(r'^$', account_settings, name='user_account_settings'),
)
