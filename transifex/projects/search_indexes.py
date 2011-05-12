import datetime
from haystack.indexes import *
from haystack import site

from transifex.projects.models import Project


class ProjectIndex(RealTimeSearchIndex):

    text = CharField(document=True, use_template=True)

    def get_queryset(self):
        """Used when the entire index for model is updated."""
        # Do not index private projects
        return Project.objects.filter(private=False,
            modified__lte=datetime.datetime.now())

    def get_updated_field(self):
        return 'modified'

site.register(Project, ProjectIndex)