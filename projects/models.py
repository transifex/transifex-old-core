from django.db import models
from django.db.models import permalink
import tagging
from tagging.fields import TagField
from tagging.models import Tag


class Project(models.Model):
    """ A project is a resource holding some content """
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    long_description = models.TextField(null=True, max_length=1000)
    slug = models.SlugField(prepopulate_from=("name",), unique=True)

    homepage = models.CharField(blank=True, max_length=255)
    feed = models.CharField(blank=True, max_length=255)
      
    repository = models.CharField(blank=True, max_length=255)
    repository_type = models.CharField(blank=True, max_length=10)
    repository_web = models.CharField(blank=True, null=True, max_length=255)
    branches = models.CharField(blank=True, max_length=255)
    report_bugs = models.CharField(blank=True, max_length=255)
    added = models.DateField(blank=True, null=True)
    last_updated = models.DateField(blank=True, null=True)
    tags = TagField()
    
    class Meta:
        ordering = ('name',)

    class Admin:
        pass

    def __unicode__(self):
        return u'%s' % self.full_name
  
    @property
    def full_name(self):
        return u'%s' % (self.name)
  
    @permalink
    def get_absolute_url(self):
        return ('project_detail', None, { 'slug': self.slug })

    def set_tags(self, tags):
        Tag.objects.update_tags(self, tags)

    def get_tags(self):
        return Tag.objects.get_for_object(self)
    
# Tagging

tagging.register(Project)