from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.decorators import login_required
from tagging.views import tagged_object_list

from projects.feeds import LatestProjects, ProjectFeed
from projects.models import Project
from projects.permissions import pr_component_submit_file
from projects.views.project import *
from projects.views.component import *
from projects.views.permission import *
from projects.views.review import *
from projects.views.team import *

from txcommon.decorators import one_perm_required_or_403
from webtrans.wizards import TransFormWizard

project_list = {
    'queryset': Project.objects.all(),
    'template_object_name': 'project',
}

project_detail = {
    'extra_context': {'project_overview': True},
}
project_detail.update(project_list)


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
        regex = '^p/(?P<param>[-\w]+)/components/feed/$',
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
    #url(
        #regex = '^p/(?P<project_slug>[-\w]+)/access/rq/add/$',
        #view = project_add_permission_request,
        #name = 'project_add_permission_request'),
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
        kwargs = project_detail),
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
    url(
        regex = '^p/(?P<slug>[-\w]+)/timeline/$',
        view = project_timeline,
        name = 'project_timeline',
        kwargs = {'queryset': Project.objects.all(),
                  'template_object_name': 'project',
                  'template_name': 'projects/project_timeline.html',
                  'extra_context': {'project_timeline': True},},),
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


# Teams
urlpatterns += patterns('',
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/teams/add/$',
        view = team_create,
        name = 'team_create',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/team/(?P<language_code>[-_@\w]+)/edit/$',
        view = team_update,
        name = 'team_update',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/teams/$',
        view = team_list,
        name = 'team_list',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/team/(?P<language_code>[-_@\w]+)/$',
        view = team_detail,
        name = 'team_detail',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/team/(?P<language_code>[-_@\w]+)/delete/$',
        view = team_delete,
        name = 'team_delete',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/team/(?P<language_code>[-_@\w]+)/request/$',
        view = team_join_request,
        name = 'team_join_request',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/team/(?P<language_code>[-_@\w]+)/approve/(?P<username>[-\w]+)/$',
        view = team_join_approve,
        name = 'team_join_approve',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/team/(?P<language_code>[-_@\w]+)/deny/(?P<username>[-\w]+)/$',
        view = team_join_deny,
        name = 'team_join_deny',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/team/(?P<language_code>[-_@\w]+)/withdraw/$',
        view = team_join_withdraw,
        name = 'team_join_withdraw',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/team/(?P<language_code>[-_@\w]+)/leave/$',
        view = team_leave,
        name = 'team_leave',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/teams/request/$',
        view = team_request,
        name = 'team_request',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/team/(?P<language_code>[-_@\w]+)/approve/$',
        view = team_request_approve,
        name = 'team_request_approve',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/team/(?P<language_code>[-_@\w]+)/deny/$',
        view = team_request_deny,
        name = 'team_request_deny',),
)

# Reviews
urlpatterns += patterns('',
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/reviews/$',
        view = review_list,
        name = 'review_list',),
    url(
        regex = '^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/reviews/(?P<id>\d+)/modify/$',
        view = review_modify,
        name = 'review_modify',),
)

#TODO: Make this setting work throughout the applications
if getattr(settings, 'ENABLE_WEBTRANS', True):
    urlpatterns += patterns('',
        url(
            regex = ('^p/(?P<project_slug>[-\w]+)/c/(?P<component_slug>[-\w]+)/'
                    'edit/(?P<filename>(.*))$'),
            # It needs to pass through both 'login_required'
            view = login_required(TransFormWizard(key=None, form_list=[])),
            name = 'component_edit_file',),
        )
