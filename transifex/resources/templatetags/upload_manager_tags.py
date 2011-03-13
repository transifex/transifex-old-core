# -*- coding: utf-8 -*-
from django import template
from django.template.defaultfilters import slugify
from transifex.txcommon.utils import get_url_pattern
from transifex.resources.forms import CreateResourceForm, ResourceTranslationForm
from transifex.resources.models import Resource

register = template.Library()


@register.inclusion_tag("resources/upload_create_resource_form.html")
def upload_create_resource_form(request, project, prefix='create_form'):
    """
    Render a form that uses StorageFile field to upload files. It creates a
    resource after the form ve validated, extract the file strings as
    sourceentities on the fly.

    The parameter 'prefix' can be used to add a prefix to the form name and
    its sub-fields.
    """
    resource = None
    if request.method == 'POST' and request.POST.get('create_resource', None):
        create_resource_form = CreateResourceForm(request.POST, prefix=prefix)
        if create_resource_form.is_valid():
            resource = create_resource_form.save(commit=False)
        display_form=True

        # If we have a resource in the creation form, check if a we already
        # have a resource with this slug in the db.
        if resource:
            try:
                Resource.objects.get(
                    slug = slugify(resource.source_file.name),
                    project = project
                )
            except Resource.DoesNotExist:
                pass
            else:
                # if the resource exists, modify slug in order to force the
                # creation of a new resource.
                slug = slugify(resource.source_file.name)
                identifier = Resource.objects.filter(project=project,
                    slug__icontains = "%s_" % slug ).count() + 1
                resource.slug = "%s_%s" % (slug, identifier)

    else:
        create_resource_form = CreateResourceForm(prefix=prefix,
            initial={'source_file':['en', ""]})
        display_form=False


    api_project_files = get_url_pattern('api_project_files')
    return {
          'project' : project,
          'resource': resource,
          'create_resource_form': create_resource_form,
          'display_form': display_form,
          'api_project_files': api_project_files,
    }


@register.inclusion_tag("resources/upload_resource_translation_button.html")
def upload_resource_translation_button(request, resource, language=None,
     prefix='button', translate_online=False):
    """
    Render a StorageFile field to upload translation and insert them into a
    resource on the fly.

    If the 'language' is passed, the field won't render the language select
    field for choosing the language.

    The parameter 'prefix' can be used to add a prefix to the field name and
    its sub-fields.

    If the parameter translate online is given, a new button will appear next
    to the upload button which onclick will redirect the user to lotte.
    """
    if language:
        initial={'resource_translation':[language.code, ""]}
    else:
        initial={}

    if request.method == 'POST' and request.POST.get('resource_translation', None):
        resource_translation_form = ResourceTranslationForm(request.POST,
            language=language, prefix=prefix, initial=initial)
        if resource_translation_form.is_valid():
            resource = resource_translation_form.save(commit=False)
    else:
        resource_translation_form = ResourceTranslationForm(language=language,
            prefix=prefix, initial=initial)

    api_resource_storage = get_url_pattern(
        'api_resource_storage')

    return {
          'project': resource.project,
          'resource': resource,
          'language' : language,
          'resource_translation_form': resource_translation_form,
          'api_resource_storage': api_resource_storage,
          'translate_online': translate_online
    }
