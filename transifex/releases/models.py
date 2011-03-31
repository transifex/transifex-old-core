# -*- coding: utf-8 -*-
import os
from datetime import datetime
import markdown

from django.conf import settings
from django.core.cache import cache
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from django.db import models, IntegrityError
from django.db.models import permalink
from django.utils.html import escape

from transifex.txcommon.log import log_model
from transifex.resources.utils import invalidate_template_cache
from transifex.resources.models import RLStats

# Config settings for the "All Resources" release (refer to
# transifex.releases.handlers for more info).
# FIXME: Some of the following strings should be i18n-ized. It seems that
#        this isn't working right now.
RELEASE_ALL_DATA = {
    'slug': 'all-resources',
    'name': 'All Resources',
    'description': "A collection of all the resources of this project (auto-managed by Transifex)"}

# List of slugs which are reserved and should not be used by users.
RESERVED_RELEASE_SLUGS = [RELEASE_ALL_DATA['slug'],]


class Release(models.Model):

    """
    A release of a project, as in 'a set of specific resources'.

    Represents the packaging and releasing of a software project (big or
    small) on a particular date, for which makes sense to track
    translations across the whole release.

    Examples of Releases is Transifex 1.0, GNOME 2.26, Fedora 10, etc.
    """

    slug = models.SlugField(_('Slug'), max_length=30,
        help_text=_('A short label to be used in the URL, containing only '
                    'letters, numbers, underscores or hyphens.'))
    name = models.CharField(_('Name'), max_length=50,
        help_text=_('A string like a name or very short description.'))
    description = models.CharField(_('Description'),
        blank=True, max_length=255,
        help_text=_('A sentence or two describing the object.'))
    long_description = models.TextField(_('Long description'),
        blank=True, max_length=1000,
        help_text=_('Use Markdown syntax.'))
    homepage = models.URLField(blank=True, verify_exists=False)

    release_date = models.DateTimeField(_('Release date'),
        blank=True, null=True,
        help_text=_('When this release will be available.'))
    stringfreeze_date = models.DateTimeField(_('String freeze date'),
        blank=True, null=True,
        help_text=_("When the translatable strings will be frozen (no strings "
                    "can be added/modified which affect translations."))
    develfreeze_date = models.DateTimeField(_('Devel freeze date'),
        blank=True, null=True,
        help_text=_("The last date packages from this release can be built "
                    "from the developers. Translations sent after this date "
                    "will not be included in the released version."))

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    # Normalized fields
    long_description_html = models.TextField(_('HTML Description'),
        blank=True, max_length=1000,
         help_text=_('Description in HTML.'), editable=False)

    # Relations
    project = models.ForeignKey('projects.Project', verbose_name=_('Project'), related_name='releases')

    resources = models.ManyToManyField('resources.Resource',
        verbose_name=_('Resources'), related_name='releases',
        blank=False, null=False)

    def __unicode__(self):
        return u'%s: %s' % (self.project.name, self.name)

    def __repr__(self):
        return _('<Release: %(rel)s (Project %(proj)s)>') % {
            'rel': self.name,
            'proj': self.project.name}

    @property
    def full_name(self):
        #return "%s: %s" % (self.project.name, self.name)
        return "%s.%s" % (self.project.slug, self.slug)

    class Meta:
        unique_together = ("slug", "project")
        verbose_name = _('release')
        verbose_name_plural = _('releases')
        ordering  = ('name',)
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        desc_escaped = escape(self.long_description)
        self.long_description_html = markdown.markdown(desc_escaped)
        created = self.created
        super(Release, self).save(*args, **kwargs)

        for stat in RLStats.objects.by_release_aggregated(self):
            invalidate_template_cache("release_details",
                self.pk, stat.object.id)

    @permalink
    def get_absolute_url(self):
        return ('release_detail', None,
                { 'project_slug': self.project.slug,
                 'release_slug': self.slug })

log_model(Release)
