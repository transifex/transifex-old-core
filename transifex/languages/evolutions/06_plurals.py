#----- Evolution for languages
from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('Language', 'pluralequation', models.CharField, initial='', max_length=255),
    AddField('Language', 'nplurals', models.SmallIntegerField, initial=0),
    AddField('Language', 'specialchars', models.CharField, initial='', max_length=255)
]
#----------------------