# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from transifex.projects.models import Project

class Gtranslate(models.Model):
    """
    Control integration with google translate service.
    """

    available_services=(
        ('', '-' * 20),
        ('GT', 'Google Translate'),
        # ('BT', 'Bing Translator'),
    )

    api_key = models.CharField(
        max_length=255, verbose_name=_("API key"), blank=True,
        help_text=_("The API key for the auto-translate service.")
    )
    service_type=models.CharField(
        max_length=2, verbose_name=_("Service"),
        choices=available_services, blank=True,
        help_text=_("The service you want to use for auto-translation.")
    )
    project = models.OneToOneField(
        Project, unique=True,
        verbose_name=_("Project"),
        help_text=_("The project this setting applies to.")
    )

    def __unicode__(self):
        return unicode(self.project)

