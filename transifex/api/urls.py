from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import OAuthAuthentication

from api.handlers import *

#TODO: Implement full support for OAUTH and refactor URLs!
auth = OAuthAuthentication(realm='Happix API')

project_handler = Resource(handler=ProjectHandler, authentication=auth)
tresource_handler = Resource(TResourceHandler)

urlpatterns = patterns('',
    url(r'^projects/(?P<id>\d+)/$', project_handler),
    url(r'^projects/(?P<project_id>\d+)/resources/(?P<tresource_id>\d+)/$',
        tresource_handler),
    url(r'^projects/(?P<project_id>\d+)/resources/(?P<tresource_id>\d+)/languages/(?P<lang_code>\w+)/$',
        tresource_handler),
)
