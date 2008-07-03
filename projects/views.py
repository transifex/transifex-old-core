from django.newforms import ModelForm
from models import Project

class ProjectForm(ModelForm):
    class Meta:
        model = Project
