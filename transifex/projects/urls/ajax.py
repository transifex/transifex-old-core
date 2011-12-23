# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

from transifex.projects.views.project import project_outsourcing_projects
from transifex.projects.views.hub import hub_associate_project_toggler
from transifex.projects.urls import PROJECT_URL_PARTIAL

# Project
urlpatterns = patterns('',
    url(
        regex = PROJECT_URL_PARTIAL+r'access/outsourcing/$',
        view = project_outsourcing_projects,
        name = 'project_outsourcing_projects'),
    url(
        regex = PROJECT_URL_PARTIAL+r'access/outsourcing/association/$',
        view = hub_associate_project_toggler,
        name = 'hub_associate_project_toggler'),
)



