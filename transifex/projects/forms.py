from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink
from django.conf import settings
from django.contrib.auth.models import User

from projects.models import Project, Component
from txcommon.validators import ValidRegexField

class ProjectForm(forms.ModelForm):
    maintainers = forms.ModelMultipleChoiceField(
        queryset=User.objects.order_by('username'))

    class Meta:
        model = Project
        exclude = ('anyone_submit',)


class ProjectAccessSubForm(forms.ModelForm):

    access_control_form = forms.BooleanField(widget=forms.HiddenInput, 
                                             initial=True)

    class Meta:
        model = Project
        fields = ('anyone_submit','access_control_form',)


class ComponentForm(forms.ModelForm):
    # TODO: Figure out how to keep this synced to Component.file_filter
    file_filter = ValidRegexField(initial='po/.*', max_length=50,
        help_text=_("A regex to filter the exposed files. Eg: 'po/.*'"))

    class Meta:
        model = Component
        exclude = ('allows_submission', 'submission_type',)


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
    submission_type = forms.ChoiceField(label=_('Submit to'), required=False,
        help_text=_("Choose how this component should handle submissions of files."
                    "The options here are available based on the component type"))

    class Meta:
        model = Component
        fields = ['allows_submission', 'submission_type',]

    def __init__(self, *args, **kwargs):
        super(ComponentAllowSubForm, self).__init__(*args, **kwargs)
        if kwargs['instance']:
            codebase_type = kwargs['instance'].unit.type
            self.fields["submission_type"].choices = \
                settings.SUBMISSION_CHOICES[codebase_type].items()


