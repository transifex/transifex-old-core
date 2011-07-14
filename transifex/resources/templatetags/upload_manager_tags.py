# -*- coding: utf-8 -*-
from django import template
from django.db import transaction
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.defaultfilters import slugify
from django.forms.util import ErrorList
from transifex.txcommon.utils import get_url_pattern
from transifex.languages.models import Language
from transifex.resources.forms import CreateResourceForm, ResourceTranslationForm
from transifex.resources.models import Resource
from transifex.resources.backends import ResourceBackend, \
        ResourceBackendError, content_from_uploaded_file

register = template.Library()


@transaction.commit_manually
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
    display_form = False
    if request.method == 'POST' and request.POST.get('create_resource', None):
        cr_form = CreateResourceForm(
            request.POST, request.FILES, prefix=prefix
        )
        if cr_form.is_valid():
            try:
                lang_code = cr_form.cleaned_data['source_lang']
                source_lang = Language.objects.by_code_or_alias(lang_code)
                name = cr_form.cleaned_data['name']
            except Language.DoesNotExist, e:
                msg = _("Invalid language selected.")
                cr_form._errors['source_lang'] = ErrorList([msg, ])
            else:
                slug = slugify(name)

                # Check if we already have a resource with this slug in the db.
                try:
                    Resource.objects.get(slug=slug, project=project)
                except Resource.DoesNotExist:
                    pass
                else:
                    # if the resource exists, modify slug in order to force the
                    # creation of a new resource.
                    slug = slugify(name)
                    identifier = Resource.objects.filter(
                        project=project, slug__icontains="%s_" % slug
                    ).count() + 1
                    slug = "%s_%s" % (slug, identifier)
                method = cr_form.cleaned_data['i18n_method']
                content = content_from_uploaded_file(request.FILES)
                rb = ResourceBackend()
                try:
                    rb.create(
                        project, slug, name, method, source_lang, content,
                        user=request.user
                    )
                except ResourceBackendError, e:
                    transaction.rollback()
                    cr_form._errors['source_file'] = ErrorList([e.message, ])
                    display_form=True
                else:
                    transaction.commit()
                    display_form = False
                    resource = Resource.objects.get(slug=slug, project=project)
        else:
            display_form=True
    else:
        cr_form = CreateResourceForm(
            prefix=prefix, initial={'source_lang': 'en'}
        )
        display_form = False

    return {
          'project' : project,
          'resource': resource,
          'create_resource_form': cr_form,
          'display_form': display_form,
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
