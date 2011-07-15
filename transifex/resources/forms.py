from uuid import uuid4
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from transifex.txcommon.exceptions import FileCheckError
from transifex.languages.models import Language
from transifex.resources.formats.registry import registry
from transifex.languages.models import Language
from transifex.resources.models import Resource
from transifex.resources.formats.core import ParseError
from transifex.resources.backends import ResourceBackend, \
        ResourceBackendError, content_from_uploaded_file
from transifex.storage.models import StorageFile

class ResourceForm(forms.ModelForm):

    sourcefile = forms.FileField(label="Source File", required=False)

    def __init__(self, *args, **kwargs):
        super(ResourceForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        # if form is edit form, disable the source_language selection
        if instance and instance.id:
            self.fields['source_language'].required = False
            self.fields['source_language'].widget.attrs['disabled'] = 'disabled'

    class Meta:
        model = Resource
        exclude = ('project', 'resource_group', 'i18n_type')

    def clean_source_language(self):
        """
        In the clean function, we make sure that it's not possible to edit the
        source_language field from an edit form.
        """
        instance = getattr(self, 'instance', None)
        if instance:
            return instance.source_language
        else:
            return self.cleaned_data.get('source_language', None)


class CreateResourceForm(forms.ModelForm):
    """Form to create a new resource."""

    i18n_choices = sorted(registry.descriptions(), key=lambda m: m[1])
    i18n_choices.insert(0, ('', '-' * 10))
    language_choices = [(l.code, l) for l in Language.objects.all()]

    source_file = forms.FileField(label=_("Resource File"))
    i18n_method = forms.ChoiceField(
        label=_("I18N Type"), choices=i18n_choices,
        help_text=_(
            "The type of i18n method used in this resource (%s)" % \
                ', '.join(sorted(m[1] for m in registry.descriptions()))
        )
    )
    source_lang = forms.ChoiceField(
        label=_('Source Language'), choices=language_choices,
        help_text=_("The source language of this Resource.")
    )

    class Meta:
        model = Resource
        fields = ('name', 'source_file', 'i18n_method', 'source_lang')


class ResourceTranslationForm(forms.Form):
    """
    Form to to be used for creating new translations.
    """

    language_choices = [(l.code, l) for l in Language.objects.all()]
    language_choices.insert(0, ('', '-' * 10))

    translation_file = forms.FileField(label=_("Translation File"))
    target_language = forms.ChoiceField(
        label=_('Language'), choices=language_choices,
        help_text=_("The language of the translation.")
    )


class ResourcePseudoTranslationForm(forms.Form):
    """Form to be used for getting pseudo translation files"""
    
    pseudo_type = forms.ChoiceField(label=_("Pseudo type"), required=True, 
        choices=[(k, v) for k, v in settings.PSEUDO_TYPES.items()], 
        widget=forms.widgets.RadioSelect, initial='MIXED',
        help_text=_("For more info about each pseudo translation type, please "
            "refer to the docs."))