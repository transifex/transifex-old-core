from django import forms
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from transifex.languages.models import Language
from transifex.teams.models import Team, TeamRequest
from transifex.txcommon.widgets import SelectWithDisabledOptions

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

        # Lets filter the language field based on the teams already created.
        # We don't need to enable a language if there is a team for it already.
        # Also, when editing the team details the language must not be changeable
        # to other complete different languages. It only accepts changing
        # language among languages with the same general code, such as pt,
        # pt_BR, pt_PT.
        instance = kwargs.get('instance', None)
        if instance:
            # Getting general language code. 'pt_BR' turns into 'pt'
            general_code = instance.language.code.split('_')[0]

            # Create list of languages to be disabled excluding the current
            # language and also languages for the same general code that do not
            # have a team already created for the related project.
            self.disabled_langs = Language.objects.exclude(
                Q(code=instance.language.code) |
                ~Q(teams__project=project), Q(code__startswith=general_code)
                ).values_list('pk', flat=True)

            # We don't need an empty label
            self.fields["language"].empty_label = None
        else:
            # Create list of languages to be disabled excluding the current
            # language_code and also the languega of teams already created.
            self.disabled_langs = Team.objects.filter(project=project).exclude(
                language__code=language_code).values_list('language__pk', flat=True)

        # Setting custom widget with list of ids that should be disabled
        self.fields["language"].widget = SelectWithDisabledOptions(
            choices=[(l.pk, l) for l in Language.objects.all()],
            disabled_choices=self.disabled_langs)

    def clean_language(self):
        """Make sure language doesn't get a invalid value."""
        data = self.cleaned_data['language']
        if isinstance(data, Language):
            pk = data.pk
        else:
            pk = int(data)
        if pk in self.disabled_langs:
            raise forms.ValidationError(_(u'Enter a valid value.'))
        return data

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

        # Create list of languages to be disabled excluding the current
        # language_code and also the languega of teams already created.
        self.disabled_langs = Team.objects.filter(project=project).exclude(
            language__code=language_code).values_list('language__pk', flat=True)

        # Setting custom widget with list of ids that should be disabled
        self.fields["language"].widget = SelectWithDisabledOptions(
            choices=[(l.pk, l) for l in Language.objects.all()],
            disabled_choices=self.disabled_langs)

    def clean_language(self):
        """Make sure language doesn't get a invalid value."""
        data = self.cleaned_data['language']
        if isinstance(data, Language):
            pk = data.pk
        else:
            pk = int(data)
        if pk in self.disabled_langs:
            raise forms.ValidationError(_(u'Enter a valid value.'))
        return data