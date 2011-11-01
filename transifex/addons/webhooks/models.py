# -*- coding: utf-8 -*-

"""
Models for the web hook addon.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _
from transifex.txcommon.validators import validate_http_url


class WebHook(models.Model):
    """A model for web hooks.

    Each project may have one web hook with a URL to hit whenever on of the
    translations is changed.
    """

    project = models.ForeignKey(
        'projects.Project', related_name='webhook', verbose_name=_('Project'),
        help_text=_('The id of the project for the web hook.')

    )
    url = models.URLField(
        verbose_name=_('URL'), validators=[validate_http_url, ],
        help_text=_('The URL to send the notification to.')
    )

    def __unicode__(self):
        return '<Webhoook for %s: %s>' % (self.project.slug, self.url)

