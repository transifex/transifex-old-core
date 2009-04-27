from django import forms
from django.db.models.fields.related import OneToOneField

from tarball.models import Tarball
from txcommon.models import inclusive_fields

class TarballForm(forms.ModelForm):
    class Meta:
        model = Tarball
        exclude = ('name',)

class TarballSubForm(forms.ModelForm):
    class Meta:
        model = Tarball
        exclude = ('name',) + tuple(
            field.name 
            for model in Tarball.__bases__
            for field in inclusive_fields(model)
        )
