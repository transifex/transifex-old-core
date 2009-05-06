from django import forms

from codebases.models import Unit

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['type',]
