#----- Evolution for projects
from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('POFile', 'rev', models.CharField, initial=None,
        max_length=64, null=True)
]
#----------------------
