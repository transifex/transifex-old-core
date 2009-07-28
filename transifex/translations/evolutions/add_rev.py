#----- Evolution for projects
from django_evolution.mutations import *
from txcommon.db.models import IntegerTupleField

MUTATIONS = [
    AddField('POFile', 'rev', IntegerTupleField, initial=None,
        max_length=64, null=True)
]
#----------------------
