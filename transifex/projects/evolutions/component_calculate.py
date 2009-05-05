#----- Evolution for projects
from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('Component', 'should_calculate', models.BooleanField, initial=True)
]
#----------------------
