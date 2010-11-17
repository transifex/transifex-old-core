from uuid import uuid4
from django import forms
from django.utils.translation import ugettext_lazy as _
from transifex.languages.models import Language
from transifex.resources.formats import get_i18n_type_from_file
from transifex.storage.fields import StorageFileField
from transifex.storage.models import StorageFile
from transifex.storage.widgets import StorageFileWidget
from transifex.resources.models import Resource
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
        exclude = ('project', 'resource_group', 'source_file', 'i18n_type')

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

    def clean(self):
        """
        Check if provided file is a valid file and can be handled by Transifex
        """
        cleaned_data = self.cleaned_data
        file = None
        language = cleaned_data['source_language']
        if cleaned_data.has_key('sourcefile'):
            file = cleaned_data['sourcefile']

        if file:
            # Check if we can handle the file with an existing parser
            sf = StorageFile()
            sf.uuid = str(uuid4())
            sf.name = file.name
            fh = open(sf.get_storage_path(), 'wb')
            file.seek(0)
            fh.write(file.read())
            fh.flush()
            fh.close()

            sf.size = file.size
            sf.language = language

            sf.update_props()
            sf.save()

            parser = sf.find_parser()
            if not parser:
                raise forms.ValidationError("File doesn't seem to be in a"
                    " valid format.")
            try:
                # Try to do an actual parsing to see if file is valid
                fhandler = parser(filename=sf.get_storage_path())
                fhandler.set_language(language)
                fhandler.contents_check(fhandler.filename)
                fhandler.parse_file(is_source=True)
            except Exception,e:
                sf.delete()
                raise forms.ValidationError("Could not import file: %s" % str(e))

            sf.delete()

        return cleaned_data

    def save(self, user=None, force_insert=False, force_update=False, commit=True):
        m = super(ResourceForm, self).save(commit=False)

        if commit:


            cleaned_data = self.cleaned_data
            file = None
            language = cleaned_data['source_language']
            if cleaned_data.has_key('sourcefile'):
                file = cleaned_data['sourcefile']

            if file:
                sf = StorageFile()
                sf.uuid = str(uuid4())
                sf.name = file.name
                fh = open(sf.get_storage_path(), 'wb')
                file.seek(0)
                fh.write(file.read())
                fh.flush()
                fh.close()

                sf.size = file.size
                sf.language = language

                sf.update_props()
                sf.save()

                parser = sf.find_parser()

                try:
                    # Try to do an actual parsing to see if file is valid
                    fhandler = parser(filename=sf.get_storage_path())
                    fhandler.set_language(language)
                    fhandler.bind_resource(self.instance)
                    fhandler.contents_check(fhandler.filename)
                    fhandler.parse_file(is_source=True)
                    fhandler.save2db(is_source=True, user=user)
                except:
                    raise

                # Try to set the i18n type. Problem is that we only check
                # filename instead of mime type. we should probably update the
                # function to use python magic as well
                try:
                    m.i18n_type = get_i18n_type_from_file(file.name)
                except:
                    pass

                m.save()

        return m


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
