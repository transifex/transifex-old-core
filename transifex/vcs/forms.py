from django import forms
from django.db.models.fields.related import OneToOneField

from txcommon.models import inclusive_fields
from vcs.models import VcsUnit

class VcsUnitForm(forms.ModelForm):
    class Meta:
        model = VcsUnit
        exclude = ('name',)

class VcsUnitSubForm(forms.ModelForm):
    class Meta:
        model = VcsUnit
        exclude = ('name',) + tuple(
            field.name 
            for model in VcsUnit.__bases__
            for field in inclusive_fields(model)
        )
