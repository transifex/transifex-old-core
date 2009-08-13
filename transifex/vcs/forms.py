from django.conf import settings
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
    type = forms.CharField(widget=forms.HiddenInput, required=False)
    
    def __init__(self, *args, **kwargs):
        codebase_type = None
        instance = kwargs.get('instance', None)
        # If editing an existent codebase
        if instance:
            codebase_type = instance.type
        else:
            # If a request for saving a new codebase
            try:
                codebase_type = args[0]['unit-type']
            except TypeError:
                pass
        super(VcsUnitSubForm, self).__init__(*args, **kwargs)
        # Check it the codebase_type has branch support
        if codebase_type and codebase_type in settings.BRANCH_SUPPORT \
            and not settings.BRANCH_SUPPORT[codebase_type]:
            self.fields['branch'].required = False
        # Set the attr id of the branch field
        self.fields['branch'].widget.attrs['id']='branch' 


    class Meta:
        model = VcsUnit
        exclude = tuple(
            field.name 
            for model in VcsUnit.__bases__
            for field in inclusive_fields(model, except_fields=['root', 'type'])
        )

    def clean(self):
        cleaned_data = self.cleaned_data
        branch = cleaned_data.get("branch")
        codebase_type = cleaned_data.get("type")
        if branch and not self.fields['branch'].required \
            and not settings.BRANCH_SUPPORT[codebase_type]:
            msg = _(u"This type of repository does not accept branch")
            raise forms.ValidationError(msg)
        return cleaned_data