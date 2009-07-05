from django import forms

class POFileSubmissionForm(forms.Form):
    
    description = forms.CharField(widget=forms.Textarea,
        help_text="Write a short description about the po file.")
    submit_pofile = forms.FileField(
        help_text="Select some po file to upload.")
