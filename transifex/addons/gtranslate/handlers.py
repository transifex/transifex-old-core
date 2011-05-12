# -*- coding: utf-8 -*-

from django import forms
from django.db.models import get_model
from django.db.models.signals import post_init
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from transifex.txcommon.log import logger
from transifex.projects.signals import project_created, project_form_init, project_form_save


def add_gtranslate(sender, form, **kwargs):
    project = form.instance
    GtModel = get_model('gtranslate', 'Gtranslate')
    try:
        gtranslate = GtModel.objects.get(project=project)
        use_gtranslate = gtranslate.use_gtranslate
    except GtModel.DoesNotExist, e:
        use_gtranslate = True

    form.fields['gtranslate'] = forms.BooleanField(
        label=_("Use google translate service"),
        initial = use_gtranslate, required=False,
        help_text=_("Check to the use Google Translation Service")
    )


def save_gtranslate(sender, form, instance, **kwargs):
    project = instance
    GtModel = get_model('gtranslate', 'Gtranslate')
    gtranslate, created = GtModel.objects.get_or_create(project=project)
    gtranslate.use_gtranslate = form.cleaned_data['gtranslate']
    gtranslate.save()


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
    project_form_init.connect(add_gtranslate)
    project_form_save.connect(save_gtranslate)
    project_created.connect(set_gtranslate_use)

