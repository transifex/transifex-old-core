#----- Evolution for translations
from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('POFile', 'language_code', models.CharField, max_length=20, null=True)
]
#----------------------