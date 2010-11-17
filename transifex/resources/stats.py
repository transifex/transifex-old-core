from django.core.cache import cache
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.releases.models import Release
from transifex.resources.models import Resource, Translation, SourceEntity
from transifex.resources.utils import *
from transifex.addons.rlstats.models import RLStats

class StatsList:
    """
    Class representing a list of Stats objects for a specific language.
    """

    @property
    def available_languages(self):
        # FIXME: Find a way to calculate project teams as languages
        return Language.objects.filter(
            id__in=RLStats.objects.filter(
            resource__in=self.resources).values('language'))

    @property
    def available_languages_without_teams(self):
        return Language.objects.filter(
            id__in=RLStats.objects.filter(
            resource__in=self.resources, translated__gt=0).values('language'))

    def aggregate_resources(self, language):
        return RLStats.objects.aggregate_resources(self.resources, language)

    def aggregate_languages(self, resource, languages=None):
        return RLStats.objects.aggregate_languages(resource, languages or
            self.available_languages)

    def resource_stats_for_language(self, language):
        for resource in self.resources:
            s = RLStats.objects.get_for_resource(resource=resource,language=language)
            yield s

    @property
    def language_stats(self):
        for lang in self.available_languages:
            yield self.aggregate_resources(lang)

    @property
    def resource_stats(self):
        for resource in self.resources:
            yield self.aggregate_languages(resource)


class ResourceStatsList(StatsList):
    """Wrapper to initialize a StatsList instance based on a resource."""

    def __init__(self, resource):
        self.resources = [ resource ]

class ProjectStatsList(StatsList):

    """Wrapper to initialize a StatsList instance based on a project."""
    def __init__(self, project):
        self.resources = project.resources.all()

class ReleaseStatsList(StatsList):
    """Wrapper to initialize a StatsList instance based on a release."""
    def __init__(self, release):
        self.resources = release.resources.all()

