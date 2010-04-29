# -*- coding: utf-8 -*-
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from projects.models import Project, Component
from projects.permissions import pr_project_private_perm
from txcommon.context_processors import site_url_prefix_processor
from txcommon.decorators import one_perm_required_or_403

def view_project_widgets(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if project.private:
        raise PermissionDenied
    components = Component.objects.filter(project = project, _unit__last_checkout__isnull = False)
    if len(components) > 0:
        default_component = components[0]
    else:
        default_component = None
    return render_to_response("project_widgets.html",
        {
            'project' : project,
            'project_widgets' : True,
            'default_component' : default_component,
            'components' : components,
        },
        RequestContext(request, {}, [site_url_prefix_processor]))