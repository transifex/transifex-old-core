from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
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
        """
        All available languages for the resource set associated with this
        StatsList. This list includes team languages that may have 0 translated
        entries.
        """
        return Language.objects.filter(
            id__in=RLStats.objects.filter(
            resource__in=self.resources).values('language'))

    @property
    def available_languages_without_teams(self):
        """
        All languages for the resource set that have at least one translation.
        """
        return Language.objects.filter(
            id__in=RLStats.objects.filter(
            resource__in=self.resources, translated__gt=0).values('language'))

    def aggregate_resources(self, language):
        """
        Helper function for the language_stats property.
        """
        return RLStats.objects.aggregate_resources(self.resources, language)

    def aggregate_languages(self, resource, languages=None):
        """
        Helper function for the resource_stats property.
        """
        return RLStats.objects.aggregate_languages(resource, languages)

    def resource_stats_for_language(self, language):
        """
        Get the statistics for a specific language/resource combination.
        """
        for resource in self.resources:
            s = RLStats.objects.get_for_resource(resource=resource,language=language)
            yield s

    @property
    def language_stats(self):
        """
        Get statistics for each available language. If there's more than 1
        resource, their statistics are aggregated.
        """
        for lang in self.available_languages:
            yield self.aggregate_resources(lang)

    @property
    def resource_stats(self):
        """
        Get statistics for each available resource.
        """
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
    def __init__(self, release, show_from_private_projects=True):
        if show_from_private_projects:
             self.resources = release.resources.all()
        else:
             self.resources = release.resources.all().filter(
                project__private=False)


class PrivateReleaseStatsList(StatsList):
    """Wrapper to initialize a StatsList instance based on a release."""
    def __init__(self, release, user):
        self.object = release
        if user in ( None, AnonymousUser()):
            self.resources = []
        else:
            self.resources = Resource.objects.for_user(user).filter(
                releases=release, project__private=True
            ).distinct()
