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

from languages.models import Language

Translation = get_model('resources', 'Translation')
SourceEntity = get_model('resources', 'SourceEntity')

from txcommon.log import logger, log_model

class Release(models.Model):

    """
    A release of a project, as in 'a set of specific components'.
    
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
        return u'%s (%s)' % (self.name, self.project.name)

    def __repr__(self):
        return _('<Release: %(rel)s (Project %(proj)s)>') % {
            'rel': self.name,
            'proj': self.project.name}
    
    @property
    def full_name(self):
        #return "%s (%s)" % (self.name, self.project.name)
        return "%s.%s" % (self.project.slug, self.slug)

    @property
    def total_entities(self):
        """
        Return the total number of SourceEntity objects to be translated.
        """
        cache_key = ('rsscount.%s.%s' % (self.project.slug, self.slug))
        rssc = cache.get(cache_key)
        if not rssc:
            rssc = SourceEntity.objects.filter(resource__releases=self).count()
            cache.set(cache_key, rssc)
        return rssc

    def last_translation(self, language=None):
        """
        Return the last translation for this Release for the given language.

        If None language value then return in all languages avaible the last 
        translation.
        """
        if language:
            if isinstance(language, str):
                language = Language.objects.by_code_or_alias(language)
            t = Translation.objects.filter(resource__releases=self,
                language=language, rule=5).order_by('-last_update')
        else:
            t = Translation.objects.filter(resource__releases=self,
                rule=5).order_by('-last_update')
        if t:
            return t[0]
        return None

    @property
    def available_languages(self):
        """
        Return the languages with at least one Translation of a SourceEntity for
        this Release.
        """
        language_ids = Translation.objects.filter(
            resource__releases=self).values_list(
            'language', flat=True).distinct()
        return Language.objects.filter(id__in=language_ids).distinct()

    def num_translated(self, language):
        """
        Return the number of translated entries for all resources in the 
        release for the given language.
        """
        if not isinstance(language, Language):
            language = Language.objects.by_code_or_alias(language)

        translations = Translation.objects.filter(resource__releases=self,
            language=language, rule=5).values_list('source_entity', flat=True)

        return len(SourceEntity.objects.filter(id__in=translations))

    def num_untranslated(self, language):
        """
        Return the number of untranslated entries for all resources in the 
        release for the given language.
        """
        if not isinstance(language, Language):
            language = Language.objects.by_code_or_alias(language)

        translations = Translation.objects.filter(resource__releases=self,
            language=language, rule=5).values_list('source_entity', flat=True)

        return len(SourceEntity.objects.filter(
            resource__releases=self).exclude(id__in=translations))

    def trans_percent(self, language):
        """
        Return the percent of translated strings for this Release for the 
        given language.
        """
        t = self.num_translated(language)
        try:
            return (t * 100 / self.total_entities)
        except ZeroDivisionError:
            return 100

    def untrans_percent(self, language):
        """
        Return the percent of untranslated strings for this Release for the 
        given language.
        """
        return (100 - self.trans_percent(language))

    class Meta:
        unique_together = ("slug", "project")
        verbose_name = _('release')
        verbose_name_plural = _('releases')
        ordering  = ('name',)
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        import markdown
        from cgi import escape
        desc_escaped = escape(self.long_description)
        self.long_description_html = markdown.markdown(desc_escaped)
        created = self.created
        super(Release, self).save(*args, **kwargs)

    @permalink
    def get_absolute_url(self):
        return ('release_detail', None,
                { 'project_slug': self.project.slug,
                 'release_slug': self.slug })

log_model(Release)
