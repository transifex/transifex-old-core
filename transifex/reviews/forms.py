from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

class POFileSubmissionForm(forms.Form):
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows':2, 'cols':50}),
        help_text=_("Write a short blurb for your review request."))
    review_file = forms.FileField(label='File for review',
        help_text=_("Select a translation file for review."))


