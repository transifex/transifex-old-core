from django import forms

class POFileSubmissionForm(forms.Form):
    
    description = forms.CharField(widget=forms.Textarea,
        help_text="Write a short description about the po file.")
    review_file = forms.FileField(
        help_text="Select some po file to upload.")
