#----- Evolution for translations
from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    ChangeField('POFile', 'is_pot', initial=None, db_index=True),
    ChangeField('POFile', 'filename', initial=None, db_index=True)
]
#----------------------
