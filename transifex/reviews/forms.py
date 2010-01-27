from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from threadedcomments.forms import FreeThreadedCommentForm

class POFileSubmissionForm(forms.Form):
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows':2, 'cols':50}),
        help_text=_("Write a short blurb for your review request."))
    review_file = forms.FileField(label='File for review',
        help_text=_("Select a translation file for review."))


class AuthenticatedCommentForm(FreeThreadedCommentForm):
    def __init__(self, user, *args, **kwargs):
        super(AuthenticatedCommentForm, self).__init__(*args, **kwargs)
        self.fields['comment'].widget.attrs.update({'rows': 4, 'cols': 70})
        self.fields['markup'].widget = forms.HiddenInput()
        self.fields['email'].widget = forms.HiddenInput(
            attrs={'autocomplete': 'off',
                   'value' : user.email}
            )
        self.fields['name'].widget = forms.HiddenInput()
        self.fields['name'].initial = user
        self.fields['website'].widget = forms.HiddenInput()
