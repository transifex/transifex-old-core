from django.conf.urls.defaults import *
from models import Project
from feeds import LatestProjects
from txc.projects.views import * 

project_list = {
    'queryset': Project.objects.all(),
    "template_object_name" : "project",
}

feeds = {
    'latest': LatestProjects,
}

urlpatterns = patterns('',
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
     {'feed_dict': feeds}, 'feed'),
)

urlpatterns += patterns('django.views.generic',
    url(
        regex = '^add/$',
        view = 'create_update.create_object',
        name = 'project_add',
        kwargs = {'model': Project}),
    url(
        regex = '^edit/(?P<slug>[-\w]+)/$',
        view = 'create_update.update_object',
        name = 'project_edit',
        kwargs = {'model': Project,
                  'template_object_name': 'project'}),
    url(
        regex = '^delete/(?P<slug>[-\w]+)/$',
        view = 'create_update.delete_object',
        name = 'project_delete',
        kwargs = {'model': Project,
                  'template_object_name': 'project',
                  'post_delete_redirect': '/projects'}),
    url(
        regex = '^(?P<slug>[-\w]+)/$',
        view = 'list_detail.object_detail',
        name = 'project_detail',
        kwargs = project_list,
        ),
    url (
        regex = '^$',
        view = 'list_detail.object_list',
        kwargs = project_list,
        name = 'project_list'),
)

# Components
urlpatterns += patterns('',
    url(
        regex = '^(?P<slug>[-\w]+)/add-component$',
        view = component_create_object,
        name = 'component_add',),
        
    url (
        regex = '^(?P<slug>[-\w]+)/components/added$',
        view = 'django.views.generic.list_detail.object_detail',
        kwargs = {'object_list': project_list,
                  'message': 'Component added.' },
        name = 'component_added'),

    url(
        regex = '^(?P<project_slug>[-\w]+)/(?P<component_slug>[-\w]+)$',
        view = component_detail,
        kwargs = project_list,
        name = 'component_detail'),
)
