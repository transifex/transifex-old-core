# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from projects.models import Project
from views import user_timeline, project_timeline

urlpatterns = patterns('',
    url(
        regex = r'^accounts/timeline/$',
        view = user_timeline,
        name='user_timeline'),

    url(
        regex = '^projects/p/(?P<slug>[-\w]+)/timeline/$',
        view = project_timeline,
        name = 'project_timeline',
        kwargs = {'queryset': Project.objects.all(),
                  'template_object_name': 'project',
                  'template_name': 'timeline/timeline_project.html',
                  'extra_context': {'project_timeline': True},},),

)
