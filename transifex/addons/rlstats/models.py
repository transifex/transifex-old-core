# -*- coding: utf-8 -*-

import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from transifex.resources.models import Resource, Translation, SourceEntity
from transifex.languages.models import Language

class RLStatsManager(models.Manager):
    def get_for_resource(self, resource, language):
        """
        Stats class for single resource with some extra values
        """
        # Create a fake object to hold the results
        stats = lambda: None
        # Init attrs
        stats.wordcount = resource.wordcount
        stats.total_entities = resource.total_entities
        stats.language = language
        stats.available_languagess = Language.objects.filter(id__in=RLStats.objects.filter(
            resource=resource).values_list('language', flat=True))
        s, created = RLStats.objects.get_or_create(resource=resource, language=language)
        stats.resource = resource

        if created:
            s.calculate_translated()

        stats.translated = s.translated
        stats.untranslated = s.untranslated
        stats.last_update = s.last_update
        stats.last_committer = s.last_committer if s.last_committer_id else None

        return stats

    def get_for_project(self, project, language):
        """
        Aggregate statistics for all resources in a project
        """
        resources = project.resources.all()
        return self.aggregate_resources(resources, language)

    def get_for_release(self, release, language):
        """
        Aggregate statistics for all resources in a release
        """
        resources = release.resources.all()
        return self.aggregate_resources(resources, language)

    def aggregate_resources(self, resources, language):
        """
        Aggregate statistics for a list of resources in a specific language
        """
        # Create a fake object to hold the results
        stats = lambda: None
        # Init attrs
        stats.translated = 0
        stats.untranslated = 0
        stats.last_update = None
        stats.last_committer = None
        stats.wordcount = 0
        stats.total_entities = 0
        stats.language = language
        stats.available_languages = Language.objects.filter(id__in=RLStats.objects.filter(
            resource__in=resources).values_list('language', flat=True))
        # Aggregate for all statistics
        for r in resources:
            stats.total_entities += r.total_entities
            stats.wordcount += r.wordcount
            s, created = RLStats.objects.get_or_create(resource=r, language=language)
            if created:
                s.calculate_translated()
            stats.translated += s.translated
            stats.untranslated += s.untranslated
            if not stats.last_update or s.last_update > stats.last_update:
                stats.last_update = s.last_update
                stats.last_committer = s.last_committer if s.last_committer_id else None

        return stats

    def aggregate_languages(self, resource, languages=None):
        """
        Aggregate statistics of a single resource for many languages
        """
        # Create a fake object to hold the results
        stats = lambda: None
        # Init attrs
        stats.translated = 0
        stats.untranslated = 0
        stats.last_update = None
        stats.last_committer = None
        stats.wordcount = resource.wordcount
        stats.total_entities = resource.total_entities
        stats.resource = resource
        stats.available_languages = Language.objects.filter(id__in=RLStats.objects.filter(
            resource=resource).values_list('language', flat=True))
        if not languages:
            languages = stats.available_languages

        for lang in languages:
            try:
                s = RLStats.objects.get(resource=resource, language=lang)
            except RLStats.DoesNotExist:
                continue
            stats.translated += s.translated
            stats.untranslated += s.untranslated
            if not stats.last_update or s.last_update > stats.last_update:
                stats.last_update = s.last_update
                stats.last_committer = s.last_committer if s.last_committer_id else None

        return stats

    def get_or_create(self, **kwargs):
        obj, created = self.get_query_set().get_or_create(**kwargs)
        if created:
            obj.calculate_translated()
            obj.update_last_translation()
        return obj, created

class RLStats(models.Model):
    """
    Resource-Language statistics object.
    """

    # Fields
    translated = models.IntegerField(_("Translated Entities"), blank=False,
        null=False, default=0, help_text="The number of translated entities"
        " in a language for a specific resource.")
    untranslated = models.IntegerField(_("Untranslated Entities"), blank=False,
        null=False, default=0, help_text="The number of untranslated entities"
        " in a language for a specific resource.")
    last_update = models.DateTimeField(_("Last Update"), auto_now=True,
        default=None,
        help_text="The datetime that this language was last updated.")
    last_committer = models.ForeignKey(User, blank=False, null=True,
        default=None,
        verbose_name=_('Last Committer'), help_text="The user associated with"
        " the last change for this language.")

    # Foreign Keys
    resource = models.ForeignKey(Resource, blank=False, null=False,
        verbose_name="Resource", help_text="The resource the statistics are"
        " associated with.")
    language = models.ForeignKey(Language, blank=False, null=False,
        verbose_name="Language", help_text="The language these statistics"
        " refer to.")

    objects = RLStatsManager()

    def __unicode__(self):
        return "%s stats for %s" % ( self.resource.slug, self.language.code)

    class Meta:
        unique_together = ('resource', 'language',)
        ordering  = ['resource',]
        order_with_respect_to = 'resource'

    def update_last_translation(self, save=True):
        lt = Translation.objects.filter(language=self.language,
            source_entity__resource=self.resource).select_related(
            'last_update', 'user').order_by('-last_update')[:1]
        if lt:
            if save:
                self.last_update = lt[0].last_update
                self.last_committer = lt[0].user
                self.save()
            return lt[0].last_update, lt[0].user

        return None, None

    def calculate_translated(self, save=True):
        """
        Calculate translated/untranslated entities.
        """
        trans_ids = Translation.objects.filter(language=self.language,
            source_entity__resource=self.resource).values_list('source_entity', flat=True)
        translated = SourceEntity.objects.filter(id__in=trans_ids).values('id').count()
        untranslated = SourceEntity.objects.filter(resource=self.resource
            ).exclude(id__in=trans_ids).values('id').count()

        if save:
            self.untranslated = untranslated
            self.translated = translated
            self.save()

        return translated, untranslated

    def update_now(self, user=None):
        """
        Update the last update and last committer.
        """
        self.last_update = datetime.datetime.now()
        if user:
            self.last_committer = user

        self.save()
