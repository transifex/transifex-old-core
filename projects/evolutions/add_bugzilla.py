#----- Evolution for projects
from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('Project', 'bug_tracker', models.URLField, initial='', max_length=200)
]
#----------------------
