from django.views.generic import create_update, list_detail
from django.shortcuts import get_object_or_404
from txc.projects.models import *

component_list = {
    'queryset': Component.objects.all(),
    "template_object_name" : "component",
}


def component_create_object(request, slug):

    from txc.projects.models import Project, Component
    project = get_object_or_404(Project, slug__iexact=slug)

    # Use the object_list view for the heavy lifting.
    return create_update.create_object(
        request,
        template_name = "projects/component_form.html",
        extra_context = {"project" : project},
        model =  Component,
    )

def component_detail(request, project_slug, component_slug, *args, **kwargs):

    #TODO: Make this one query
    project = get_object_or_404(Project, slug__iexact=project_slug)
    component = get_object_or_404(Component, slug__exact=component_slug,
                                  project=project)

    # Use the object_list view for the heavy lifting.
    return list_detail.object_detail(
        request,
        object_id=component.id,
        queryset = Component.objects.all(),
        template_object_name = "component",
        template_name = "projects/component_detail.html",
        extra_context = {'project': component.project}
    )
component_detail.__doc__ = list_detail.object_detail.__doc__
