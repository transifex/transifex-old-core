# -*- coding: utf-8 -*-

from django.db.models import get_model
from django.conf import settings
from transifex.projects.signals import project_created, project_deleted


def delete_gtranslate(sender, **kwargs):
    """
    Delete a Gtranslate object after its corresponding projet has been deleted.
    """
    GtModel = get_model('gtranslate', 'Gtranslate')
    try:
        gt = GtModel.objects.get(project=sender)
        gt.delete()
    except GtModel.DoesNotExit, e:
        pass


def connect():
    project_deleted.connect(delete_gtranslate)

