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
from transifex.resources.backends import ResourceBackend, FormatsBackend, \
        ResourceBackendError, FormatsBackendError, content_from_uploaded_file

register = template.Library()


@transaction.commit_manually
@register.inclusion_tag("resources/upload_create_resource_form.html")
def upload_create_resource_form(request, project, prefix='create_form'):
    """Form for creating a new resource."""
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
    """Form to add a translation.

    If the parameter translate online is given, a new button will appear next
    to the upload button which onclick will redirect the user to lotte.
    """
    uploaded = False
    show_form = False
    if language:
        initial={'target_language': [language.code, ]}
    else:
        initial={}

    if request.method == 'POST' and request.POST.get('upload_translation', None):
        rt_form = ResourceTranslationForm(
            request.POST, request.FILES, prefix=prefix, initial=initial
        )
        if rt_form.is_valid():
            target_lang = rt_form.cleaned_data['target_language']
            content = content_from_uploaded_file(request.FILES)
            try:
                save_translation(resource, target_lang, request.user, content)
                uploaded = True
            except FormatsBackendError, e:
                rt_form._errors['translation_file'] = ErrorList([e.message, ])
                show_form = True
    else:
        rt_form = ResourceTranslationForm(
            prefix=prefix, initial=initial
        )

    return {
          'project': resource.project,
          'resource': resource,
          'language' : language,
          'resource_translation_form': rt_form,
          'translate_online': translate_online,
          'uploaded': uploaded,
          'show_form': show_form,
    }


@transaction.commit_on_success
def save_translation(resource, target_language, user, content):
    """Save a new translation file for the resource."""
    fb = FormatsBackend(resource, target_language, user)
    return fb.import_translation(content)

