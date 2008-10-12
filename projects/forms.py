from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink

from projects.models import Component, Unit
from vcs.forms import UnitForm

class ComponentForm(forms.ModelForm):
    class Meta:
        model = Component

    def __init__(self, project, *args, **kwargs):
        super(ComponentForm, self).__init__(*args, **kwargs)
        projects = self.fields["project"].queryset.filter(slug=project.slug)
        self.fields["project"].queryset = projects
        self.fields["project"].empty_label = None


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        exclude= ('name',)
