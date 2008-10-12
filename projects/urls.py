from django.conf.urls.defaults import *
from django.contrib import admin

from projects.models import Project
from projects.views import * 
from feeds import LatestProjects

admin.autodiscover()

project_list = {
    'queryset': Project.objects.all(),
    "template_object_name" : "project",
}

feeds = {
    'latest': LatestProjects,
}

urlpatterns = patterns('',
    url(
        regex = r'^feeds/(?P<url>[-\w]+)/$',
        view = 'django.contrib.syndication.views.feed',
        name = 'project_feed',
        kwargs = {'feed_dict': feeds}),
)

urlpatterns += patterns('django.views.generic',
    url(
        regex = '^add/$',
        view = 'create_update.create_object',
        name = 'project_add',
        kwargs = {'model': Project}),
    url(
        regex = '^(?P<slug>[-\w]+)/edit/$',
        view = 'create_update.update_object',
        name = 'project_edit',
        kwargs = {'model': Project,
                  'template_object_name': 'project'}),
    url(
        regex = '^(?P<slug>[-\w]+)/delete/$',
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
        regex = '^(?P<project_slug>[-\w]+)/add-component/$',
        view = component_create_update,
        name = 'component_add',),
    url(
        regex = '^(?P<project_slug>[-\w]+)/(?P<component_slug>[-\w]+)/edit/$',
        view = component_create_update,
        name = 'component_edit',),
    url(
        regex = '^(?P<project_slug>[-\w]+)/(?P<component_slug>[-\w]+)/delete/$',
        view = component_delete,
        name = 'component_delete',
        kwargs = {'model': Component,
                  'template_object_name': 'component'}),
    url(
        regex = '^(?P<project_slug>[-\w]+)/(?P<component_slug>[-\w]+)/set_stats/$',
        view = component_set_stats,
        name = 'component_set_stats',),
    url (
        regex = '^(?P<slug>[-\w]+)/components/added/$',
        view = 'django.views.generic.list_detail.object_detail',
        kwargs = {'object_list': project_list,
                  'message': 'Component added.' },
        name = 'component_added'),
    url(
        regex = '^(?P<project_slug>[-\w]+)/(?P<component_slug>[-\w]+)/$',
        view = component_detail,
        kwargs = project_list,
        name = 'component_detail'),
)
