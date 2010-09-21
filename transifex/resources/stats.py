from django.core.cache import cache
from languages.models import Language
from resources.models import Resource, Translation, SourceEntity
from resources.utils import *

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

    @stats_cached_property
    def translations(self):
        """Return all translations for the related entities."""
        return Translation.objects.filter(source_entity__in=self.entities)

    @stats_cached_property
    def last_translation(self):
        """Return last translation made, independing on language."""
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


class Stats(StatsBase):
    """A low-level statistics-holding object.

    Imagine it as a row in a statistics table for a specific language,
    or in the real world, as a translation file (e.g. a specific PO file).

    Requires an iteretable of entities (e.g. a QuerySet) and a language.
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

    @property
    def available_languages(self):
        """
        Return a list of languages with at least one translation for one of 
        the given entities.
        """
        language_ids = self.translations.values_list('language__id', flat=True)
        return Language.objects.filter(id__in=language_ids).distinct()

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
    """Wrapper to initialize a StatsList instance based on a resource.

    #TODO: Override wanted methods to cache theirs results based on the 
    class attrs.
    """
    def __init__(self, resource):
        self.object = resource
        self.entities = SourceEntity.objects.filter(resource=resource)

    @property
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


class ProjectStatsList(StatsList):
    """Wrapper to initialize a StatsList instance based on a project.

    #TODO: Override wanted methods to cache theirs results based on the 
    class attrs.
    """
    def __init__(self, project):
        self.object = project
        self.entities = SourceEntity.objects.filter(resource__project=project)


class ReleaseStatsList(StatsList):
    """Wrapper to initialize a StatsList instance based on a release.

    #TODO: Override wanted methods to cache theirs results based on the 
    class attrs.
    """
    def __init__(self, release):
        self.object = release
        self.entities = SourceEntity.objects.filter(resource__releases=release)

