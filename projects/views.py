from django.http import Http404
from django.views.generic import create_update
from models import Project, Component

def component_create_object(request, slug):

    # Look up the publisher (and raise a 404 if it can't be found).
    try:
        project = Project.objects.get(slug__exact=slug)
    except Project.DoesNotExist:
        raise Http404

    # Use the object_list view for the heavy lifting.
    return create_update.create_object(
        request,
        template_name = "projects/component_form.html",
        extra_context = {"project" : project},
        model =  Component,
    )
