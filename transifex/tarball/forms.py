from django import forms

from tarball.models import Tarball
from txcommon.models import inclusive_fields
from txcommon.validators import ValidTarBallUrl

class TarballForm(forms.ModelForm):
    class Meta:
        model = Tarball
        exclude = ('name',)

class TarballSubForm(forms.ModelForm):

    root = ValidTarBallUrl()

    class Meta:
        model = Tarball
        exclude = tuple(
            field.name 
            for model in Tarball.__bases__
            for field in inclusive_fields(model, except_fields=['root'])
        )
