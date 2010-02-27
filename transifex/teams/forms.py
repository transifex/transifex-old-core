from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from transifex.teams.models import Team, TeamRequest

from ajax_select.fields import AutoCompleteField, AutoCompleteSelectMultipleField


class TeamSimpleForm(forms.ModelForm):
    coordinators = AutoCompleteSelectMultipleField('users', required=True,
        help_text=_("Coordinators are people that can manage the members of the "
                    "team, for example. Search for usernames."))

    members = AutoCompleteSelectMultipleField('users', required=False,
        help_text=_("Members are actually people that can submit translations. "
                    "Search for usernames."))
    class Meta:
        model = Team
        fields = ('language', 'coordinators', 'members', 'mainlist', 'project',
            'creator')

    def __init__(self, project, language_code=None, *args, **kwargs):
        super(TeamSimpleForm, self).__init__(*args, **kwargs)
        self.fields['project'].widget = forms.HiddenInput()
        self.fields['project'].initial = project.pk
        self.fields['creator'].widget = forms.HiddenInput()

        # Lets filter the language field based on the teams already created
        # We don't need to list a language if there is a team for it already
        # Also, when editing a team detail the language must not be changeable
        instance = kwargs.get('instance', None)
        if instance:
            filtered_langs = self.fields["language"].queryset.filter(
                pk=instance.language.pk)
            self.fields["language"].empty_label = None
        else:
            used_langs = Team.objects.filter(project__pk=project.pk).exclude(
                language__code=language_code).values('language__pk').query
            filtered_langs = self.fields["language"].queryset.exclude(pk__in=used_langs)
        self.fields["language"].queryset = filtered_langs

    def clean(self):
        cleaned_data = self.cleaned_data
        coordinators = cleaned_data.get("coordinators")
        members = cleaned_data.get("members")

        if coordinators and members:
            for c in coordinators:
                if c in members:
                    user = User.objects.get(pk=c)
                    raise forms.ValidationError(_("You have the user '%s' in "
                        "both coordinators and members lists. Please drop "
                        "him/her from one of those lists.") % user)

        return cleaned_data



class TeamRequestSimpleForm(forms.ModelForm):
    class Meta:
        model = TeamRequest
        fields = ('language', 'project', 'user')

    def __init__(self, project, language_code=None, *args, **kwargs):
        super(TeamRequestSimpleForm, self).__init__(*args, **kwargs)
        self.fields['project'].widget = forms.HiddenInput()
        self.fields['project'].initial = project.pk
        self.fields['user'].widget = forms.HiddenInput()
        
        # Lets filter the language field based on the teams already created
        # We don't need to list a language if there is a team for it already
        used_langs = Team.objects.filter(project__pk=project.pk).exclude(
            language__code=language_code).values('language__pk').query
        filtered_langs = self.fields["language"].queryset.exclude(pk__in=used_langs)
        self.fields["language"].queryset = filtered_langs


