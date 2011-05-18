# -*- coding: utf-8 -*-

from django.db.models import get_model
from django.conf import settings


class Meta:
    title = "Control integration with google translate."
    author = "Apostolos Bessas"
    description = "Enables/disables translate.google.com integration for projects."


def is_gtranslate_allowed(project):
    """
    Check whether the use of the google translate service is allowed.

    It is forbidden for projects in settings.DISALLOWED_SLUGS andthose
    that outsource their access to them.
    """
    GtModel = get_model('gtranslate', 'Gtranslate')
    try:
        gt = GtModel.objects.get(project=project)
        if not gt.use_gtranslate:
            return False
    except GtModel.DoesNotExist, e:
        pass

    if project.outsource is not None and project.outsource.slug in settings.DISALLOWED_SLUGS:
        return False
    return True
