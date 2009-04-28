#----- Evolution for actionlog
from django_evolution.mutations import *
from django.conf import settings
from django.db import models

MUTATIONS = [
    AddField('LogEntry', 'object_name', models.CharField, initial='', max_length=200),
    AddField('LogEntry', 'message', models.TextField, null=True),
    AddField('LogEntry', 'action_type', models.ForeignKey, initial='', related_model='notification.NoticeType'),
    DeleteField('LogEntry', 'action_flag'),
    DeleteField('LogEntry', 'object_repr'),
    DeleteField('LogEntry', 'change_message'),
    ChangeField('LogEntry', 'user', initial=None, null=True)
]
#----------------------
