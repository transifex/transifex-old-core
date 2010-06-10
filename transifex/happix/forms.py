from django import forms
from happix.models import Resource

class ResourceForm(forms.ModelForm):

    class Meta:
        model = Resource
        exclude = ('project', 'resource_group')

