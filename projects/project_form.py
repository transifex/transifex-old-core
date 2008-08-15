from django import newforms as forms

class ProjectForm(forms.Form):
    name = forms.CharField(max_length=100)
    description = forms.CharField()
