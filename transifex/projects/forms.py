from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink

from projects.models import Project, Component
from txcommon.validators import ValidRegexField

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project

class ComponentForm(forms.ModelForm):
    # TODO: Figure out how to keep this synced to Component.file_filter
    file_filter = ValidRegexField(initial='po/.*', max_length=50,
        help_text=_("A regex to filter the exposed files. Eg: 'po/.*'"))

    class Meta:
        model = Component
        exclude = ('allows_submission',)


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


class ComponentAllowSubForm(forms.ModelForm):

    submission_form = forms.BooleanField(widget=forms.HiddenInput, initial=True)

    class Meta:
        model = Component
        fields = ['allows_submission',]

