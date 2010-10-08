from django import forms
from django.utils.translation import ugettext_lazy as _
from transifex.languages.models import Language
from transifex.storage.fields import StorageFileField
from transifex.storage.models import StorageFile
from transifex.storage.widgets import StorageFileWidget
from transifex.resources.models import Resource

class ResourceForm(forms.ModelForm):

    class Meta:
        model = Resource
        exclude = ('project', 'resource_group', 'source_file')


class CreateResourceForm(forms.ModelForm):
    """
    Form to create a resource using data from StorageFileField.
    """
    source_file = StorageFileField(label=_('Resource file'),
        help_text=_("Choose the source language for the resource and then "
        "select a file from your file system to be used as an extracting "
        "point of strings to be translated."))

    class Meta:
        model = Resource
        fields = ('source_file',)


class ResourceTranslationForm(forms.Form):
    """
    Form to to be used for creating/getting StorageFile object id on the fly,
    using StorageFileField.
    """
    def __init__(self, *args, **kwargs):
        language = kwargs.pop('language', None)
        super(ResourceTranslationForm, self).__init__(*args, **kwargs)

        self.fields['resource_translation'] = StorageFileField(
            label=_('Resource file'),
            help_text=_("Select a file from your file system to be used to "
                "fill translations for this resource."), language=language)
