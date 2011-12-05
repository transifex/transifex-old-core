from django.conf.urls.defaults import *
from gtranslate.views import autotranslate_proxy, supported_langs

urlpatterns = patterns('',
    url('^ajax/projects/p/(?P<project_slug>[-\w]+)/autotranslate/$',
        autotranslate_proxy, name='autotranslate_proxy'),
    url('^ajax/projects/p/(?P<project_slug>[-\w]+)/supportedlangs/$',
        supported_langs, name='supported_langs'),
)