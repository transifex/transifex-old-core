from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('Component', 'releases', models.ManyToManyField, null=True, related_model='txcollections.CollectionRelease')
]
