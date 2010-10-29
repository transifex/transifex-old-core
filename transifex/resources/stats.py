from django.core.cache import cache
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.releases.models import Release
from transifex.resources.models import Resource, Translation, SourceEntity
from transifex.resources.utils import *

class StatsBase:
    """A low-level statistics-holding object to inherit from.

    Requires an iterable of entities (e.g. a QuerySet).
    """

    # This object is like an identifier for caching. We only cache object
    # related stats classes, otherwise if we do it for plain querysets, we'd
    # have to evaluate them everytime. This object can hold a Resource, Project
    # or Release
    object = None

    def __init__(self, entities):
        self.entities = entities

    @property
    def available_languages(self):
        """Return a list of available languages.

        The list of languages includes the languages with at least one
        translation for one of the given entities. If ``object`` is an
        instance of ``Project`` or ``Resource`` the list will also contain
        the languages used in the related project teams of the given object.
        """
        language_ids = self.available_languages_without_teams.values_list('id', flat=True)

        team_lang_ids = None
        project = None
        if isinstance(self.object, Project):
            project = self.object
        elif isinstance(self.object, (Resource, Release)):
            project = self.object.project

        if project:
            # Check whether project has outsourced its translation access control
            if project.outsource:
                project = project.outsource

            team_lang_ids = project.team_set.values_list('language__id', 
                flat=True)

        # Extending list of language_ids as necessary.
        if team_lang_ids:
            language_ids = set(list(language_ids) + list(team_lang_ids))

        return Language.objects.filter(id__in=language_ids).distinct()

    @stats_cached_property
    def available_languages_without_teams(self):
        """
        Return a list of languages with at least one translation for one of
        the given entities.
        """
        language_ids = self.translations.values_list('language__id', flat=True)
        return Language.objects.filter(id__in=language_ids).distinct()

    @stats_cached_property
    def translations(self):
        """Return all translations for the related entities."""
        return Translation.objects.filter(source_entity__in=self.entities)

    @stats_cached_property
    def last_translation(self):
        """Return last translation made, independent of language."""
        t = self.translations.select_related('last_update', 'user'
            ).order_by('-last_update')[:1]
        if t:
            return t[0]

    @stats_cached_property
    def last_update(self):
        """
        Return the time of the last translation made, without depending on
        language.
        """
        lt = self.last_translation
        if lt:
            return lt.last_update

    @stats_cached_property
    def last_committer(self):
        """
        Return the committer of the last translation made, without depending on
        language.
        """
        lt = self.last_translation
        if lt:
            return lt.user

    @stats_cached_property
    def total_entities(self):
        """
        Return the total number of SourceEntity objects to be translated.
        """
        return self.entities.values('id').count()

    @stats_cached_property
    def wordcount(self):
        """
        Return the number of words which need translation in this resource.

        The counting of the words uses the Translation objects of the SOURCE
        LANGUAGE as set of objects. This function does not count the plural 
        strings!
        """
        wc = 0
        source_trans = Translation.objects.filter(source_entity__id__in=
            self.entities)
        for t in source_trans:
            if t:
                wc += t.wordcount
        return wc



class Stats(StatsBase):
    """A low-level statistics-holding object.

    Imagine it as a row in a statistics table for a specific language,
    or in the real world, as a translation file (e.g. a specific PO file).

    Requires an iterable of entities (e.g. a QuerySet) and a language.
    """

    def __init__(self, entities, language):
        self.entities = entities
        self.language = language

    @stats_cached_property
    def translations(self):
        return Translation.objects.filter(source_entity__in=self.entities,
            language=self.language)

    @stats_cached_property
    def num_translated(self):
        """Return the number of translated entries."""
        trans_ids = self.translations.values_list('source_entity', flat=True)
        return SourceEntity.objects.filter(id__in=trans_ids).values('id').count()

    @stats_cached_property
    def num_untranslated(self):
        """Return the number of untranslated entries."""
        trans_ids = self.translations.values_list('source_entity', flat=True)
        return SourceEntity.objects.filter(id__in=self.entities
            ).exclude(id__in=trans_ids).values('id').count()

    @stats_cached_property
    def trans_percent(self):
        """Return the percent of translated entries."""
        t = self.num_translated
        try:
            return (t * 100 / self.total_entities)
        except ZeroDivisionError:
            return 100

    @stats_cached_property
    def untrans_percent(self):
        """Return the percent of untranslated entries."""
        return (100 - self.trans_percent)

    @stats_cached_property
    def resources(self):
        """Return a list of resources related to the given entities."""
        return Resource.objects.filter(source_entities__in=self.entities
            ).distinct()


class StatsList(StatsBase):
    """Class representing a list of Stats objects (e.g. a statistics table).

    Can be overridden for more specific cases, or it can be called as-is with
    a list of entities.
    """

    def stat(self, language):
        """Return a Stat object for a specific language."""
        return Stats(entities=self.entities, language=language)


    def language_stats(self):
        """Yield a Stat object for each available language.

        Useful to render a table of available languages and their statistics.
        """
        for language in self.available_languages:
            sa = self.stat(language=language)
            sa.object = self.object
            yield sa

    def resource_stats(self):
        """Yield a Stat object for each available resource.

        It adds a resource attribute to the related StatsBase object.
        """
        resources = Resource.objects.filter(source_entities__in=self.entities
            ).distinct()
        for resource in resources:
            sa = StatsBase(resource.entities)
            sa.object = resource
            yield sa

    def resource_stats_for_language(self, language):
        """Yield a Stat object for each available resource for a given language.

        It adds a resource attribute to the related Stats object.
        """
        resources = Resource.objects.filter(source_entities__in=self.entities
            ).distinct()
        for resource in resources:
            sa = Stats(resource.entities, language)
            sa.object = resource
            yield sa


class ResourceStatsList(StatsList):
    """Wrapper to initialize a StatsList instance based on a resource."""

    def __init__(self, resource):
        self.object = resource
        self.entities = SourceEntity.objects.filter(resource=resource)


class ProjectStatsList(StatsList):

    """Wrapper to initialize a StatsList instance based on a project."""
    def __init__(self, project):
        self.object = project
        self.entities = SourceEntity.objects.filter(resource__project=project)


class ReleaseStatsList(StatsList):
    """Wrapper to initialize a StatsList instance based on a release."""
    def __init__(self, release):
        self.object = release
        self.entities = SourceEntity.objects.filter(resource__releases=release)

