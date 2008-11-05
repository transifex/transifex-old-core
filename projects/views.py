import os
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import create_update, list_detail
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import feed

from projects.models import Project, Component
from projects.forms import ComponentForm, UnitForm

# Feeds

def slug_feed(request, slug=None, param='', feed_dict=None):
    """
    Override default feed, using custom (including inexistent) slug.
    
    Provides the functionality needed to decouple the Feed's slug from
    the urlconf, so a feed mounted at "^/feed" can exist.
    
    See also http://code.djangoproject.com/ticket/6969.
    """
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)


# Override generic views to use decorator

@login_required
def project_create(*args, **kwargs):
    return create_update.create_object(*args, **kwargs)

@login_required
def project_update(*args, **kwargs):
    return create_update.update_object(*args, **kwargs)

@login_required
def project_delete(*args, **kwargs):
    return create_update.delete_object(*args, **kwargs)

@login_required
def component_create_update(request, project_slug, component_slug=None):
    """
    Create & update components. Handles associated units
    """
    project = get_object_or_404(Project, slug__iexact=project_slug)
    if component_slug:    
        component = get_object_or_404(Component, slug__iexact=component_slug)
        unit = component.unit    
    else:
        component = None
        unit = None
    if request.method == 'POST':
        component_form = ComponentForm(project, request.POST, instance=component, prefix='component')
        unit_form = UnitForm(request.POST, instance=unit, prefix='unit')
        if component_form.is_valid() and unit_form.is_valid():
            component = component_form.save(commit=False)
            unit = unit_form.save(commit=False)            
            unit.name = component.get_full_name()
            unit.save()
            component.unit = unit
            component.save()
            return HttpResponseRedirect('/projects/%s/%s' % (project.slug, component.slug))
    else:
        component_form = ComponentForm(project, instance=component, prefix='component')
        unit_form = UnitForm(instance=unit, prefix='unit')
    return render_to_response('projects/component_form.html', {
        'component_form': component_form,
        'unit_form': unit_form,
        'project' : project,
    }, context_instance=RequestContext(request))

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

@login_required
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


def component_set_stats(request, project_slug, component_slug, *args, **kwargs):
    #TODO: Make this one query
    project = get_object_or_404(Project, slug__iexact=project_slug)
    component = get_object_or_404(Component, slug__exact=component_slug,
                                  project=project)
    # Calcule statistics
    component.trans.set_stats()

    return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))


def component_raw_file(request, project_slug, component_slug, filename, *args, **kwargs):
    #TODO: Make this one query
    project = get_object_or_404(Project, slug__iexact=project_slug)
    component = get_object_or_404(Component, slug__exact=component_slug,
                                  project=project)

    try:
        content = component.trans.get_file_content(filename)
    except IOError:
        raise Http404
    filename = "%s.%s" % (component.full_name, os.path.basename(filename))

    response = HttpResponse(content, mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    return response
