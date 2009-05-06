from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.util import ErrorList

from vcs.models import VcsUnit
from txcommon.models import inclusive_fields

class VcsUnitForm(forms.ModelForm):
    class Meta:
        model = VcsUnit
        exclude = ('name',)

class VcsUnitSubForm(forms.ModelForm):
    class Meta:
        model = VcsUnit
        exclude = tuple(
            field.name 
            for model in VcsUnit.__bases__
            for field in inclusive_fields(model, except_fields=['root'])
        )

    # TODO: Make validation flexible for VCSs that does not need a branch
    # We are validating it here (in the Form) because we will need to handle
    # more then one field to make the TODO above.
    def clean(self):
        cleaned_data = self.cleaned_data
        branch = cleaned_data.get("branch")
        if not branch:
            msg = _(u"This type of repository needs a branch")
            self._errors["branch"] = ErrorList([msg])
        return cleaned_data