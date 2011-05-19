# -*- coding: utf-8 -*-

from django.db.models import get_model
from django.conf import settings
from transifex.projects.signals import project_created, project_deleted


def set_gtranslate_use(sender, **kwargs):
    """
    Set the use of google translate on project creation.
    """
    GtModel = get_model('gtranslate', 'Gtranslate')
    gt = GtModel(project=sender)
    for p in GtModel.objects.filter(use_gtranslate=False):
        if sender.slug == p or (sender.outsource is not None and sender.outsource == p):
            gt.use_gtranslate = False
            break
    else:
        gt.use_gtranslate = True
    gt.save()


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
    project_created.connect(set_gtranslate_use)
    project_deleted.connect(delete_gtranslate)

