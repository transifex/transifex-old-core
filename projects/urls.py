from django.conf.urls.defaults import *
from txc.projects.models import *


project_list = {
  'queryset': Project.objects.all(),
}


urlpatterns = patterns('',
  url(
    regex   = '^(?P<slug>[-\w]+)/$',
    view    = 'django.views.generic.list_detail.object_detail',
    kwargs  = project_list,
    name    = 'project_detail',
  ),
  url (
    regex   = '^$',
    view    = 'django.views.generic.list_detail.object_list',
    kwargs  = project_list,
    name    = 'project_list',
  ),
)

