#----- Evolution for txcollections
from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    ChangeField('Collection', 'slug', initial=None, unique=True)
]
#----------------------

