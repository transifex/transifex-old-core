from django import forms
from happix.models import TResource

class TResourceForm(forms.ModelForm):

    class Meta:
        model = TResource
        exclude = ('project', 'tresource_group')

