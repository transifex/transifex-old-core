from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink

from projects.models import Component
from vcs.forms import UnitForm

def get_component_form(project, *args, **kwargs):
    """
    Return a ModelForm for Component, specific to a Project.
    
    Django's generic views require a ModelForm class (not an
    instance of it), so we need to create it dynamically.
    This method does exactly that and returns the class.

    """
    
    class ComponentForm(forms.ModelForm):
        
        """
        A Project's ModelForm for the Component model.
        
        The fields of this form are modified to fit the particular
        Project (stored in ``project`` variable).

        """
        
        unit_form = UnitForm()
        
        root = unit_form.fields['root']
        type = unit_form.fields['type']
        branch = unit_form.fields['branch']
        web_frontend = unit_form.fields['web_frontend']
    
        class Meta:
            model = Component
            
        def __init__(self, *args, **kwargs):
            super(ComponentForm, self).__init__(*args, **kwargs)
            projects = self.fields["project"].queryset.filter(slug=project.slug)
            self.fields["project"].queryset = projects
            self.fields["project"].empty_label = None
                
        def save(self, *args, **kwargs):
            obj = super(ComponentForm, self).save(*args, **kwargs)
            return obj
            
    #        Order fields
    #        from django.utils.datastructures import SortedDict
    #        (From: http://www.djangosnippets.org/snippets/759/)
    #        order = ('project', 'name', 'description', 'slug')
    #        tmp = dict.copy(self.fields)
    #        self.fields = SortedDict()
    #        for item in order:
    #            self.fields[item] = tmp[item]
    #        self.fields.update(tmp)

    return ComponentForm