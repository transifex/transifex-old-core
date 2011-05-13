# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from transifex.projects.models import Project

class Gtranslate(models.Model):
    """
    Control integration with google translate service.
    """

    use_gtranslate = models.BooleanField(
        default=False, verbose_name=_("Enable google translate"),
        help_text=_("Enable integration with google translate service.")
    )
    project = models.OneToOneField(
        Project, unique=True,
        verbose_name=_("Project"),
        help_text=_("The project this setting applies to.")
    )

    def __unicode__(self):
        return unicode(self.project)

