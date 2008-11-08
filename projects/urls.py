from django.conf.urls.defaults import *
from django.contrib import admin
from tagging.views import tagged_object_list

from projects.models import Project
from projects.views import * 
from feeds import (LatestProjects, ProjectFeed)

admin.autodiscover()

project_list = {
    'queryset': Project.objects.all(),
    "template_object_name" : "project",
}

feeds = {
    'latest': LatestProjects,
    'project': ProjectFeed,
}

urlpatterns = patterns('',
    url(
        regex = r'^feed/$',
        view = 'projects.views.slug_feed',
        name = 'project_latest_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'latest'}),
    url(
        regex = r'^(?P<param>[-\w]+)/feed/$',
        view = 'projects.views.slug_feed',
        name = 'project_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'project'}),
)

urlpatterns += patterns('django.views.generic',
    url(
        regex = '^add/$',
        view = project_create,
        name = 'project_create',
        kwargs = {'model': Project}),
    url(
        regex = '^(?P<slug>[-\w]+)/edit/$',
        view = project_update,
        name = 'project_edit',
        kwargs = {'model': Project,
                  'template_object_name': 'project'}),
    url(
        regex = '^(?P<slug>[-\w]+)/delete/$',
        view = project_delete,
        name = 'project_delete',
        kwargs = {'model': Project,
                  'template_object_name': 'project',}),
    url(
        regex = '^(?P<slug>[-\w]+)/$',
        view = 'list_detail.object_detail',
        name = 'project_detail',
        kwargs = project_list,),
    url (
        regex = '^$',
        view = 'list_detail.object_list',
        kwargs = project_list,
        name = 'project_list'),
    url(
        r'^tag/(?P<tag>[^/]+)/$',
        tagged_object_list,
        dict(queryset_or_model=Project, allow_empty=True,
             template_object_name='project'),
        name='project_tag_list'),

)


# Components
urlpatterns += patterns('',
    url(
        regex = '^(?P<project_slug>[-\w]+)/add-component/$',
        view = component_create_update,
        name = 'component_create',),
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
    url(
        regex = '^(?P<project_slug>[-\w]+)/(?P<component_slug>[-\w]+)/raw/(?P<filename>(.*))$',
        view = component_raw_file,
        name = 'component_raw_file',),
    url (
        regex = '^(?P<slug>[-\w]+)/components/added/$',
        view = 'django.views.generic.list_detail.object_detail',
        kwargs = {'object_list': project_list,
                  'message': 'Component added.' },
        name = 'component_created'),
    url(
        regex = '^(?P<project_slug>[-\w]+)/(?P<component_slug>[-\w]+)/$',
        view = component_detail,
        kwargs = project_list,
        name = 'component_detail'),
)
