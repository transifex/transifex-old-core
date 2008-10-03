from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext 
from django.views.generic import create_update, list_detail
from django.utils.translation import ugettext_lazy as _

from projects.models import Project, Component
from projects.forms import get_component_form

def component_create_object(request, slug):
    project = get_object_or_404(Project, slug__iexact=slug)
    form = get_component_form(project)
    return create_update.create_object(
        request,
        form_class=get_component_form(project),
        extra_context={'project': project})
component_create_object.__doc__ = create_update.create_object.__doc__


def component_detail(request, project_slug, component_slug, *args, **kwargs):
    project = get_object_or_404(Project, slug__iexact=project_slug)
    component = get_object_or_404(Component, slug__exact=component_slug,
                                  project=project)
    return list_detail.object_detail(
        request,
        queryset = Component.objects.all(),
        object_id=component.id,
        template_object_name = "component",
        extra_context = {'project': project}
    )
component_detail.__doc__ = list_detail.object_detail.__doc__

                                                                                                                                                                                                            
def component_edit(request, project_slug, component_slug, *args, **kwargs):
    #TODO: Make this one query
    project = get_object_or_404(Project, slug__iexact=project_slug)
    component = get_object_or_404(Component, slug__exact=component_slug,
                                  project=project)
    return create_update.update_object(
        request,
        object_id=component.id,
        form_class=get_component_form(project),
        template_object_name = "component",
        extra_context = {'project': project}
    )
component_detail.__doc__ = create_update.update_object.__doc__


def component_delete(request, project_slug, component_slug, *args, **kwargs):
    #TODO: Make this one query
    project = get_object_or_404(Project, slug__iexact=project_slug)
    component = get_object_or_404(Component, slug__exact=component_slug,
                                  project=project)
    return create_update.delete_object(
        request,
        model=Component,
        object_id=component.id,
        template_object_name = "component",
        extra_context = {'project': project},
        post_delete_redirect = '/projects/%s' % project.slug,
    )
component_detail.__doc__ = create_update.delete_object.__doc__
