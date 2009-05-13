#----- Evolution for projects
from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('Component', 'submission_type', models.CharField, initial='', max_length=10)
]
#----------------------

