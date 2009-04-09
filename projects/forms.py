from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink

from projects.models import Project, Component, VcsUnit


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project

class ComponentForm(forms.ModelForm):
    class Meta:
        model = Component

    def __init__(self, project, *args, **kwargs):
        super(ComponentForm, self).__init__(*args, **kwargs)
        projects = self.fields["project"].queryset.filter(slug=project.slug)
        self.fields["project"].queryset = projects
        self.fields["project"].empty_label = None

        # Filtering releases by the collections of the project
        collection_query = project.collections.values('pk').query
        releases = self.fields["releases"].queryset.filter(
                                           collection__id__in=collection_query)
        self.fields["releases"].queryset = releases

class UnitForm(forms.ModelForm):
    class Meta:
        model = VcsUnit
        exclude= ('name',)
