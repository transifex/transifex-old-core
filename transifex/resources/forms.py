from uuid import uuid4
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from transifex.txcommon.exceptions import FileCheckError
from transifex.languages.models import Language
from transifex.resources.formats.registry import registry
from transifex.storage.fields import StorageFileField
from transifex.storage.models import StorageFile
from transifex.storage.widgets import StorageFileWidget
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

    def __init__(self, *args, **kwargs):
        
        project = kwargs.pop('project', None)
        super(CreateResourceForm, self).__init__(*args, **kwargs)

        self.source_language = project.source_language
        
    def clean(self):
        """Check whether the language"""
        cleaned_data = self.cleaned_data
        source_file = cleaned_data.get('source_file')
        
        if self.source_language and self.source_language != source_file.language:
            msg = _("Invalid selected language.")
            self._errors["source_file"] = self.error_class([msg])
            del cleaned_data["source_file"]
        return cleaned_data


class ResourceTranslationForm(forms.Form):
    """
    Form to to be used for creating/getting StorageFile object id on the fly,
    using StorageFileField.
    """
    def __init__(self, *args, **kwargs):
        language = kwargs.pop('language', None)
        display_language = kwargs.pop('display_language', None)
        super(ResourceTranslationForm, self).__init__(*args, **kwargs)

        self.fields['resource_translation'] = StorageFileField(
            label=_('Resource file'),
            help_text=_("Select a file from your file system to be used to "
                "fill translations for this resource."), language=language,
                display_language=display_language)


class ResourcePseudoTranslationForm(forms.Form):
    """Form to be used for getting pseudo translation files"""
    
    pseudo_type = forms.ChoiceField(label=_("Pseudo type"), required=True, 
        choices=[(k, v) for k, v in settings.PSEUDO_TYPES.items()], 
        widget=forms.widgets.RadioSelect, initial='MIXED',
        help_text=_("For more info about each pseudo translation type, please "
            "refer to the docs."))