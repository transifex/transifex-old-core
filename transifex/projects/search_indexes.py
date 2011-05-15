import datetime
from haystack.indexes import *
from haystack import site

from transifex.projects.models import Project


class ProjectIndex(RealTimeSearchIndex):

    text = CharField(document=True, use_template=True)
    
    slug = CharField(model_attr='slug', null=False)
    name = CharField(model_attr='name', null=False, boost=1.125)
    description = CharField(model_attr='description', null=True) 

    # django-haystack-1.2 needs it along with the custom prepare method
    suggestions = CharField()

    def prepare(self, obj):
        prepared_data = super(ProjectIndex, self).prepare(obj)
        prepared_data['suggestions'] = prepared_data['text']
        return prepared_data

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        # Do not index private projects
        return Project.objects.exclude(private=True).filter(
            modified__lte=datetime.datetime.now())

    def get_updated_field(self):
        """Project mode field used to identify new/modified object to index."""
        return 'modified'

site.register(Project, ProjectIndex)