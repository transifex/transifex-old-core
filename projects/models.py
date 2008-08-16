import datetime

from django.db import models
from django.contrib import admin
from django.db.models import permalink
from django.forms import ModelForm

import tagging
from tagging.fields import TagField
from tagging.models import Tag


class Project(models.Model):
    """A project is a collection of translatable resources.
    
    # Create some projects
    >>> foo = Project.objects.create(slug="foo", name="Foo Project")
    >>> bar = Project.objects.create(slug="bar", name="Bar Project")
    >>> foo.name
    'Foo Project'
    >>> foo.set_tags = 'foo project'
    >>> print ' '.join(foo.get_tags())
    """

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    long_description = models.TextField(blank=True, max_length=1000,
        help_text='Use Markdown syntax.')
    long_description_html = models.TextField(blank=True, max_length=1000, 
        help_text='Description as HTML.', editable=False)
    slug = models.SlugField(unique=True, primary_key='True',
        help_text='A unique, normalized name the entry (used in URLs, etc).')
    
    num_components = models.PositiveIntegerField(default=0)

    homepage = models.CharField(blank=True, max_length=255)
    feed = models.CharField(blank=True, max_length=255,
        help_text='An RSS feed with updates on the project.')
    enabled = models.BooleanField(default=True)
    date_created = models.DateField(default=datetime.datetime.now,
                                    editable=False)
    date_modified = models.DateTimeField(editable=False)

    #tags = TagField(help_text="Separate tags with spaces.")

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return u'%s' % self.name

    @permalink
    def get_absolute_url(self):
        return ('project_detail', None, { 'slug': self.slug })

    def set_tags(self, tags):
        Tag.objects.update_tags(self, tags)

    def get_tags(self):
        return Tag.objects.get_for_object(self)

    def save(self):
        self.date_modified = datetime.datetime.now()
        super(Project, self).save()

class ProjectAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
admin.site.register(Project, ProjectAdmin)

class ProjectForm(ModelForm):
    class Meta:
        model = Project


class Component(models.Model):
    """ A component is a translatable resource. """
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    long_description = models.TextField(blank=True, max_length=1000,
        help_text='Use Markdown syntax.')
    long_description_html = models.TextField(blank=True, null=True,
        max_length=1000, help_text='Description as HTML.', editable=False)
    slug = models.SlugField(unique=True)
    
    project = models.ForeignKey(Project)
      
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
    date_created = models.DateField(default=datetime.datetime.now,
                                    editable=False)
    date_modified = models.DateTimeField(editable=False)

    #tags = TagField(help_text="Separate tags with spaces.")

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
        self.date_modified = datetime.datetime.now()
        self.long_description_html = markdown.markdown(self.long_description)
        super(Component, self).save()
        # Update de-normalized field
        self.project.num_components = self.project.component_set.count()
        self.project.save()

# Tagging

tagging.register(Project)
