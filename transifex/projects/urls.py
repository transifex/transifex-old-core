from django.conf.urls.defaults import *
from django.conf import settings
from tagging.views import tagged_object_list

from projects.models import Project
from projects.views import * 
from feeds import (LatestProjects, ProjectFeed)

project_list = {
    'queryset': Project.objects.all(),
    'template_object_name': 'project',
}

feeds = {
    'latest': LatestProjects,
    'project': ProjectFeed,
}

#TODO: Temporary until we import view from a common place
SLUG_FEED = 'projects.views.slug_feed'
urlpatterns = patterns('',
    url(
        regex = r'^feed/$',
        view = SLUG_FEED,
        name = 'project_latest_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'latest'}),
    url(
        regex = r'^(?P<param>[-\w]+)/components/feed/$',
        view = SLUG_FEED,
        name = 'project_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'project'}),
)


# Project
urlpatterns += patterns('',
    url(
        regex = '^add/$',
        view = project_create,
        name = 'project_create'),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/edit/$',
        view = project_update,
        name = 'project_edit',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/delete/$',
        view = project_delete,
        name = 'project_delete',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/access/pm/add/$',
        view = project_add_permission,
        name = 'project_add_permission'),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/access/pm/(?P<permission_pk>\d+)/delete/$',
        view = project_delete_permission,
        name = 'project_delete_permission'),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/access/rq/add/$',
        view = project_add_permission_request,
        name = 'project_add_permission_request'),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/access/rq/(?P<permission_pk>\d+)/delete/$',
        view = project_delete_permission_request,
        name = 'project_delete_permission_request'),
        
    url(regex = '^p/(?P<project_slug>[-\w]+)/access/rq/(?P<permission_pk>\d+)/approve/$',
        view = project_approve_permission_request,
        name = "project_approve_permission_request"),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/toggle_watch/$',
        view = project_toggle_watch,
        name = 'project_toggle_watch',),
)

urlpatterns += patterns('django.views.generic',
    url(
        regex = '^p/(?P<slug>[-\w]+)/$',
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
        regex = '^p/(?P<project_slug>[-\w]+)/add-component/$',
        view = component_create_update,
        name = 'component_create',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/edit/$',
        view = component_create_update,
        name = 'component_edit',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/delete/$',
        view = component_delete,
        name = 'component_delete',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/clear_cache/$',
        view = component_clear_cache,
        name = 'component_clear_cache',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/set_stats/$',
        view = component_set_stats,
        name = 'component_set_stats',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/raw/(?P<filename>(.*))$',
        view = component_file,
        name = 'component_raw_file',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/view/(?P<filename>(.*))$',
        view = component_file,
        name = 'component_view_file',
        kwargs = {'view': True },),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/toggle_lock/(?P<filename>(.*))$',
        view = component_toggle_lock_file,
        name = 'component_toggle_lock_file',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/submit/(?P<filename>(.*))$',
        view = component_submit_file,
        name = 'component_submit_file',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/toggle_watch/pofile/(?P<filename>(.*))$',
        view = component_toggle_watch,
        name = 'component_toggle_watch',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/submit/$',
        view = component_submit_file,
        name = 'component_submit_new_file',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/l/(?P<language_code>(.*))$',
        view = component_language_detail,
        name = 'component_language_detail',),
    url (
        regex = '^p/(?P<slug>[-\w]+)/component-added/$',
        view = 'django.views.generic.list_detail.object_detail',
        kwargs = {'object_list': project_list,
                  'message': 'Component added.' },
        name = 'component_created'),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/$',
        view = component_detail,
        name = 'component_detail'),
)

#TODO: Make this setting work throughout the applications
if getattr(settings, 'ENABLE_WEBTRANS', True):
    urlpatterns += patterns('',
        url(
            regex = ('^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/'
                    'edit/(?P<filename>(.*))$'),
            view = component_file_edit,
            name = 'component_edit_file',),
        )

