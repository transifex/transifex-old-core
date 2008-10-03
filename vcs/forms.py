from django import forms
from django.utils.translation import ugettext_lazy as _

from vcs.models import Unit

class UnitForm(forms.ModelForm):

    """
    Form used to handle the creation or update of a Unit.
    
    Models using Unit as an underlying element can inject this form
    into their own forms, like follows:
    
    class MyObjectForm(forms.ModelForm):
        from vcs.forms import UnitForm
        unit_form = UnitForm()
        root = unit_form.fields['root']
    
    For an example of this refer to transifex.projects.forms.
     
    """
    
    @property
    def cleaned_data(self):
        return []
    
    class Meta:
        model = Unit