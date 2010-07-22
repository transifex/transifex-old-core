from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink
from django.conf import settings
from django.contrib.auth.models import User
from django.forms import widgets
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

from ajax_select.fields import AutoCompleteSelectMultipleField

from projects.models import Project, Component, Release
from txcommon.validators import ValidRegexField

class ProjectForm(forms.ModelForm):
    maintainers = AutoCompleteSelectMultipleField('users', required=True,
        help_text=_('Search for a username'))

    class Meta:
        model = Project
        exclude = ('anyone_submit', 'outsource', 'private')


class RadioFieldRenderer(widgets.RadioFieldRenderer):
    """
    An object used by RadioSelect to enable customization of radio widgets.
    """
    def get_class(self, v, v2):
        """
        Return the string 'selected' if both values are equal.

        This is used to set a class attr on the selected radio buttom.
        """
        if v==v2:
            return 'selected'
        else:
            return ''

    def render(self):
        """Outputs a <ul> for this set of radio fields."""
        help_text = self.attrs['help_text']
        self.attrs.pop('help_text')
        return mark_safe(u'<ul>\n%s\n</ul>' % u'\n'.join(
            [u'<li class="%s"><span>%s</span><p class="helptext">%s</p></li>'
                % (self.get_class(w.value, w.choice_value),
                   force_unicode(w),
                   help_text[w.choice_value]) for w in self]))


class ProjectAccessControlForm(forms.ModelForm):
    """Form to handle the Access Control options of a project."""
    access_control_options=[
        {'free_for_all': {
            'label': _('Free for all'),
            'help_text': _("""Allow any logged-in user to submit files to my
                              project. <a href="http://www.youtube.com/watch?v=okd3hLlvvLw"
                              target="_blank">Imagine</a> all the people,
                              sharing all the world. Recommended for quick
                              translations, and when a pre-commit review
                              process is in place, e.g. when contributions are
                              submitted by email or to a separate branch."""),
            }
        },
        {'limited_access': {
            'label': _('Limited access'),
            'help_text': _("""Give access to specific people. Translations
                              teams will have access to their language's files
                              only, and global writers will have access to all
                              translation files. Recommended for most
                              projects."""),
            }
        },
        {'outsourced_access': {
            'label': _('Outsourced access'),
            'help_text': _("""Re-use another project's teams and writers by
                              delegating access control to that project. If a
                              person can contribute to that project, it can
                              contribute to this one as well. Recommended for
                              non-upstream projects such as distribution
                              packages, desktop environment modules, etc."""),
            }
        },
    ]

    # Setting up some vars based on the 'access_control_options' var
    access_control_types = []
    access_control_help = {}
    for o in access_control_options:
        for k, v in o.items():
            access_control_types.append((k, v['label']))
            access_control_help.update({k: v['help_text']})

    # Add field
    access_control = forms.ChoiceField(choices=access_control_types,
        required=True, widget=forms.RadioSelect(
            renderer=RadioFieldRenderer,
            attrs={'help_text': access_control_help }))

    class Meta:
        model = Project
        fields = ('access_control', 'outsource')

    def __init__(self, *args, **kwargs):
        super(ProjectAccessControlForm, self).__init__(*args, **kwargs)
        # Changing some field settings based on the project attr and the
        # request.DATA
        project = kwargs.get('instance', None)
        outsource_required = False
        if args:
            access_control_initial = args[0]['access_control']
            if 'outsourced_access' == access_control_initial:
                outsource_required = True
        elif project:
            if project.anyone_submit:
                access_control_initial = 'free_for_all'
            elif project.outsource:
                access_control_initial = 'outsourced_access'
                outsource_required = True
            else:
                access_control_initial = 'limited_access'

        self.fields['access_control'].initial = access_control_initial
        self.fields['outsource'].required = outsource_required

        # Filtering project list
        projects = self.fields["outsource"].queryset.exclude(slug=project.slug)
        self.fields["outsource"].queryset = projects


class ComponentForm(forms.ModelForm):
    # TODO: Figure out how to keep this synced to Component.file_filter
    file_filter = ValidRegexField(initial='po/.*', max_length=50,
        help_text=_("A regular expression to filter the exposed files. Eg: 'po/.*'"))

    class Meta:
        model = Component
        exclude = ('allows_submission', 'submission_type',)


    def __init__(self, project, *args, **kwargs):
        super(ComponentForm, self).__init__(*args, **kwargs)
        project = self.fields["project"].queryset.filter(slug=project.slug)
        self.fields["project"].queryset = project
        self.fields["project"].empty_label = None


class ComponentAllowSubForm(forms.ModelForm):

    submission_form = forms.BooleanField(widget=forms.HiddenInput, initial=True)
    submission_type = forms.ChoiceField(label=_('Submit to'), required=False,
        help_text=_("Choose how this component should handle submissions of files."
                    "The options here are available based on the component type"))

    class Meta:
        model = Component
        fields = ['allows_submission', 'submission_type',]

    def __init__(self, submission_types, *args, **kwargs):
        super(ComponentAllowSubForm, self).__init__(*args, **kwargs)
        self.fields["submission_type"].choices = submission_types


class ReleaseForm(forms.ModelForm):

    components = AutoCompleteSelectMultipleField('components', required=True,
        help_text=_('Search for a component'))

    class Meta:
        model = Release

    def __init__(self, project, *args, **kwargs):
        super(ReleaseForm, self).__init__(*args, **kwargs)
        projects = self.fields["project"].queryset.filter(slug=project.slug)
        self.fields["project"].queryset = projects
        self.fields["project"].empty_label = None


