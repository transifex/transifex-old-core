# -*- coding: utf-8 -*-
import os
from datetime import datetime
import markdown

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from django.db import models, IntegrityError
from django.db.models import permalink, get_model
from django.dispatch import Signal
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.html import escape

from authority.models import Permission
from notification.models import ObservedItem
import tagging
from tagging.fields import TagField

from codebases.models import Unit
from languages.models import Language
from vcs.models import VcsUnit
from tarball.models import Tarball
from translations.models import POFile
from txcommon.log import logger, log_model
from txcommon.utils import cached_property
from projects import signals

SourceEntity = get_model('resources', 'SourceEntity')
Translation = get_model('resources', 'Translation')


# keys used in cache
# We put it here to have them all in one place for the specific models!
PROJECTS_CACHE_KEYS = {
    "word_count": "wcount.%s",
    "source_strings_count": "sscount.%s"
}

class DefaultProjectManager(models.Manager):
    """
    This is the defautl manager of the project model (asigned to objects field).
    """

    def watched_by(self, user):
        """
        Retrieve projects being watched by the specific user.
        """
        try:
            ct = ContentType.objects.get(name="project")
        except ContentType.DoesNotExist:
            pass
        observed_projects = [i[0] for i in list(set(ObservedItem.objects.filter(user=user, content_type=ct).values_list("object_id")))]
        watched_projects = []
        for object_id in observed_projects:
            try:
                watched_projects.append(Project.objects.get(id=object_id))
            except Project.DoesNotExist:
                pass
        return watched_projects

    def maintained_by(self,user):
        """
        Retrieve projects being maintained by the specific user.
        """
        return Project.objects.filter(maintainers__id=user.id)

    def translated_by(self, user):
        """
        Retrieve projects being translated by the specific user.
        
        The method returns all the projects in which user has been granted 
        permissions to submit translations.
        """
        try:
            ct = ContentType.objects.get(name="project")
        except ContentType.DoesNotExist:
            pass
        return Permission.objects.filter(user=user, content_type=ct, approved=True)
    

class PublicProjectManager(models.Manager):
    """
    Return a QuerySet of public projects.
    
    Usage: Projects.public.all()
    """

    def get_query_set(self):
        return super(PublicProjectManager, self).get_query_set().filter(private=False)

    def recent(self):
        return self.order_by('-created')

    def open_translations(self):
        #FIXME: This should look like this, more or less:
        #open_resources = Resource.objects.filter(accept_translations=True)
        #return self.filter(resource__in=open_resources).distinct()
        return self.all()


class Project(models.Model):

    """
    A project is a group of translatable resources.

    >>> p, created = Project.objects.get_or_create(slug="foo", name="Foo Project")
    >>> p = Project.objects.get(slug='foo')
    >>> p
    <Project: Foo Project>
    >>> Project.objects.create(slug="foo", name="Foo Project")
    Traceback (most recent call last):
        ...
    IntegrityError: column slug is not unique
    >>> if created: p.delete()

    """

    private = models.BooleanField(default=False, verbose_name=_('Private'),
        help_text=_('A private project is visible only by you and your team.'
                    'Moreover, private projects are limited according to billing'
                    'plans for the user account.'))
    slug = models.SlugField(_('Slug'), max_length=30, unique=True,
        help_text=_('A short label to be used in the URL, containing only '
                    'letters, numbers, underscores or hyphens.'))
    name = models.CharField(_('Name'), max_length=50,
        help_text=_('A short name or very short description.'))
    description = models.CharField(_('Description'), blank=True, max_length=255,
        help_text=_('A sentence or two describing the object (optional).'))
    long_description = models.TextField(_('Long description'), blank=True, 
        max_length=1000,
        help_text=_('A longer description (optional). Use Markdown syntax.'))
    homepage = models.URLField(_('Homepage'), blank=True, verify_exists=False)
    feed = models.CharField(_('Feed'), blank=True, max_length=255,
        help_text=_('An RSS feed with updates to the project.'))
    bug_tracker = models.URLField(_('Bug tracker'), blank=True,
        help_text=_('The URL for the bug and tickets tracking system '
                    '(Bugzilla, Trac, etc.)'))
    anyone_submit = models.BooleanField(_('Anyone can submit'), 
        default=False, blank=False,
        help_text=_('Can anyone submit files to this project?'))

    hidden = models.BooleanField(_('Hidden'), default=False, editable=False,
        help_text=_('Hide this object from the list view?'))
    enabled = models.BooleanField(_('Enabled'),default=True, editable=False,
        help_text=_('Enable this object or disable its use?'))
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    tags = TagField(verbose_name=_('Tags'))

    # Relations
    maintainers = models.ManyToManyField(User, verbose_name=_('Maintainers'),
        related_name='projects_maintaining', blank=False, null=True)

    outsource = models.ForeignKey('Project', blank=True, null=True,
        verbose_name=_('Outsource project'),
        help_text=_('Project that owns the access control of this project.'))

    owner = models.ForeignKey(User, blank=True, null=True,
        editable=False, verbose_name=_('Owner'),
        help_text=_('The user who owns this project.'))

    # Normalized fields
    long_description_html = models.TextField(_('HTML Description'), blank=True, 
        max_length=1000,
        help_text=_('Description in HTML.'), editable=False)

    # Managers
    objects = DefaultProjectManager()
    public = PublicProjectManager()

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return _('<Project: %s>') % self.name

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        db_table  = 'projects_project'
        ordering  = ('name',)
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        """Save the object in the database."""
        long_desc = escape(self.long_description)
        self.long_description_html = markdown.markdown(long_desc)
        super(Project, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.resources.all().delete()
        super(Project, self).delete(*args, **kwargs)

    @permalink
    def get_absolute_url(self):
        return ('project_detail', None, { 'project_slug': self.slug })

    @property
    def source_strings(self):
        """
        Return the list of all the strings, belonging to the Source Language
        of the Project/Resource.
        
        CAUTION! 
        1. This function returns Translation and not SourceEntity objects!
        2. The strings may be in different source languages!!!
        3. The source strings are not grouped based on the string value.
        """
        resources = self.resources.all()
        source_strings = []
        for resource in resources:
            source_strings.extend(resource.source_strings)
        return 

    #TODO: Invalidation for cached value
    @property
    def total_entities(self):
        """Return the total number of source entities to be translated."""
        cache_key = (PROJECTS_CACHE_KEYS['source_strings_count'] % (self.project.slug,))
        sc = cache.get(cache_key)
        if not sc:
            sc = SourceEntity.objects.filter(
                resource__in=self.resources.all()).count()
            cache.set(cache_key, sc)
        return sc

    # TODO: Invalidation for cached value
    @property
    def wordcount(self):
        """
        Return the number of words which need translation in this project.
        
        The counting of the words uses the Translation objects of the source
        languages as set of objects.
        CAUTION: 
        1. The strings may be in different source languages!!!
        2. The source strings are not grouped based on the string value.
        """
        cache_key = (PROJECTS_CACHE_KEYS['word_count'] % self.project.slug)
        wc = cache.get(cache_key)
        if not wc:
            wc = 0
            resources = self.resources.all()
            for resource in resources:
                wc += resource.wordcount
            cache.set(cache_key, wc)
        return wc

    @property
    def available_languages(self):
        """
        Return the languages with at least one Translation of a SourceEntity for
        all Resources in the specific project instance.
        """
        # I put it here due to circular dependency on module
        resources = self.resources.all()
        languages = Translation.objects.filter(
            resource__in=resources).values_list(
            'language', flat=True).distinct()
        # The distinct() below is not important ... I put it just to be sure.
        return Language.objects.filter(id__in=languages).distinct()

    def translated_strings(self, language):
        """
        Return the QuerySet of source entities, translated in this language.
        
        This assumes that we DO NOT SAVE empty strings for untranslated entities!
        """
        # I put it here due to circular dependency on modules
        target_language = Language.objects.by_code_or_alias(language)
        return SourceEntity.objects.filter(resource__in=self.resources.all(),
            id__in=Translation.objects.filter(language=target_language,
                resource__in=self.resources.all(), rule=5).values_list(
                    'source_entity', flat=True))

    def untranslated_strings(self, language):
        """
        Return the QuerySet of source entities which are not yet translated in
        the specific language.
        
        This assumes that we DO NOT SAVE empty strings for untranslated entities!
        """
        # I put it here due to circular dependency on modules
        target_language = Language.objects.by_code_or_alias(language)
        return SourceEntity.objects.filter(
            resource__in=self.resources.all()).exclude(
            id__in=Translation.objects.filter(language=target_language,
                resource__in=self.resources.all(), rule=5).values_list(
                    'source_entity', flat=True))

    def num_translated(self, language):
        """
        Return the number of translated strings in all Resources of the project.
        """
        return self.translated_strings(language).count()

    def num_untranslated(self, language):
        """
        Return the number of untranslated strings in all Resources of the project.
        """
        return self.untranslated_strings(language).count()

    def trans_percent(self, language):
        """Return the percent of untranslated strings in this Resource."""
        t = self.num_translated(language)
        try:
            return (t * 100 / self.total_entities)
        except ZeroDivisionError:
            return 100

    def untrans_percent(self, language):
        """Return the percent of untranslated strings in this Resource."""
        translated_percent = self.trans_percent(language)
        return (100 - translated_percent)

tagging.register(Project, tag_descriptor_attr='tagsobj')
log_model(Project)

