# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import OAuthAuthentication

from api.handlers import *

#TODO: Implement full support for OAUTH and refactor URLs!
#auth = OAuthAuthentication(realm='Happix API')

#project_handler = Resource(handler=ProjectHandler) #, authentication=auth)
#tresource_handler = Resource(TResourceHandler)
tr = Resource(TResourceHandler)
urlpatterns = patterns('',
    url(r'^languages/$', Resource(LanguageHandler)),
#    url(r'^project/(?P<project_slug>[-\w]+)/$', project_handler),
    url(r'^project/(?P<project_slug>[-\w]+)/resources/$', tr),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/$', tr),
    url(r'^project/(?P<project_slug>[-\w]+)/resource/(?P<tresource_slug>[-\w]+)/(?P<lang_code>\w+)/$', Resource(StringHandler), name='api_resource_translation'),
    #url(r'^projects/(?P<project_id>\d+)/resources/(?P<tresource_id>\d+)/languages/(?P<lang_code>\w+)/$',
        #tresource_handler),

)
