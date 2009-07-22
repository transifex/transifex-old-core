#----- Evolution for projects
from django_evolution.mutations import *
from txcommon.models import IntegerTupleField

MUTATIONS = [
    AddField('POFile', 'rev', IntegerTupleField, initial='',
        max_length=64, null=True)
]
#----------------------
