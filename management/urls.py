from django.conf.urls.defaults import *
from models import *

hold_list = {
    'queryset': Hold.objects.all(),
}


urlpatterns = patterns('',
    url(
        regex = '^(?P<slug>[-\w]+)/$',
        view = 'django.views.generic.list_detail.object_detail',
        kwargs = hold_list,
        name = 'hold_detail',
        ),
     url (
       regex = '^add$',
       view = 'management.views.hold_create',
       name = 'hold_create',
     ),
     url (
       regex = '^$',
       view = 'django.views.generic.list_detail.object_list',
       kwargs = hold_list,
       name = 'hold_list',
     ),
)

