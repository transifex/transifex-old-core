# -*- coding: utf-8 -*-

from django.db.models import get_model
from django.conf import settings
from transifex.projects.signals import project_created


def set_gtranslate_use(sender, **kwargs):
    """
    Set the use of google translate on project creation.
    """
    GtModel = get_model('gtranslate', 'Gtranslate')
    gt = GtModel(project=sender)
    PModel = get_model('projects', 'Project')
    disallowed = ( PModel.objects.get(slug=x) for x in settings.DISALLOWED_SLUGS)
    for p in disallowed:
        if sender == p or sender.outsource == p:
            gt.use_gtranslate = False
            break
    else:
        gt.use_gtranslate = True
    gt.save()


def connect():
    project_created.connect(set_gtranslate_use)

