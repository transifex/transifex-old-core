import datetime
from haystack import indexes
from transifex.projects.models import Project

class ProjectIndex(indexes.RealTimeSearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    
    slug = indexes.CharField(model_attr='slug', null=False)
    name = indexes.CharField(model_attr='name', null=False, boost=1.125)
    description = indexes.CharField(model_attr='description', null=True)
    tags = indexes.MultiValueField()

    suggestions = indexes.FacetCharField()

    def get_model(self):
        return Project

    def prepare(self, obj):
        prepared_data = super(ProjectIndex, self).prepare(obj)
        prepared_data['suggestions'] = prepared_data['text']
        prepared_data['tags'] = [tag.name for tag in obj.tagsobj]
        return prepared_data

    def index_queryset(self):
        """Used when the entire index for model is updated."""
        # Do not index private projects
        return self.get_model().objects.exclude(private=True).filter(
            modified__lte=datetime.datetime.now())

    def should_update(self, instance, **kwargs):
        """
        Determine if an object should be updated in the index.
        """
        if instance.private:
            return False
        return True

    # TODO: Newer version of django-haystack has support for .using() and this
    # method needs to be refactored once using that.
    def update_object(self, instance, using=None, **kwargs):
        """
        Update the index for a single object. Attached to the class's
        post-save hook.
        """
        # Check to make sure we want to index this first.
        if self.should_update(instance, **kwargs):
            self._get_backend(using).update(self, [instance])
        else:
            # self.should_update checks whether a project is private or not.
            # If it was open and now it's private, it should be removed from the
            # indexing. Private projects should NOT be indexed for now.
            self.remove_object(instance, using, **kwargs)

    def get_updated_field(self):
        """Project mode field used to identify new/modified object to index."""
        return 'modified'