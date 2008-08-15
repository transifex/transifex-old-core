from django.db import models
from django.contrib import admin
from django.db.models import permalink
import tagging
from tagging.fields import TagField
from tagging.models import Tag



class Project(models.Model):
    """ A project is a resource holding some content """
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    long_description = models.TextField(null=True, max_length=1000,
        help_text='Use Markdown syntax.')
    long_description_html = models.TextField(blank=True, null=True,
        max_length=1000, help_text='Description as HTML.')
    slug = models.SlugField(unique=True)

    homepage = models.CharField(blank=True, max_length=255)
    feed = models.CharField(blank=True, max_length=255,
        help_text='An RSS feed with updates on the project.')
      
    repository = models.CharField(blank=True, max_length=255,
        help_text="The URL of the project's source repository")
    repository_type = models.CharField(blank=True, max_length=10,
        help_text='cvs, svn, hg, git, ...')
    repository_web = models.CharField(blank=True, null=True, max_length=255,
        help_text="A URL to the versioning system's web front-end")
    branches = models.CharField(blank=True, max_length=255,
        help_text='Space-separated list of branch names')
    report_bugs = models.CharField(blank=True, max_length=255,
        help_text="A URL to the project's bugzilla, trac, etc")
    enabled = models.BooleanField(default=True)
    added = models.DateField(blank=True, null=True, editable=False)
    last_updated = models.DateField(blank=True, null=True, editable=False)
    


    class Meta:
        ordering = ('name',)

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

    def save(self):
        import markdown
        self.long_description_html = markdown.markdown(self.long_description)
        super(Entry, self).save() # Call the "real" save() method.

class ProjectAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
admin.site.register(Project, ProjectAdmin)

# Tagging

tagging.register(Project)
