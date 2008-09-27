from datetime import datetime
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.db.models import permalink
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField
from tagging.models import Tag

from statistics.models import POStatistic, Language

class Project(models.Model):
    """A project is a collection of translatable resources.

    >>> p = Project.objects.create(slug="foo", name="Foo Project")
    >>> p = Project.objects.get(slug='foo')
    >>> p
    <Project: Foo Project>
    >>> Project.objects.create(slug="foo", name="Foo Project")
    Traceback (most recent call last):
        ...
    IntegrityError: column slug is not unique
    >>> p.delete()
    """

    slug = models.SlugField(unique=True)

    name = models.CharField(max_length=50)
    description = models.CharField(blank=True, max_length=255)
    long_description = models.TextField(blank=True, max_length=1000,
        help_text=_('Use Markdown syntax.'))
    long_description_html = models.TextField(blank=True, max_length=1000, 
        help_text=_('Description as HTML.'), editable=False)
    homepage = models.CharField(blank=True, max_length=255)
    feed = models.CharField(blank=True, max_length=255,
        help_text=_('An RSS feed with updates on the project.'))

    num_components = models.PositiveIntegerField(editable=False, default=0)

    hidden = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    created = models.DateField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        db_table  = 'projects_project'
        ordering  = ('name',)
        get_latest_by = 'created'

    def __repr__(self):
        return _('<Project: %s>') % self.name
  
    def __unicode__(self):
        return u'%s' % self.name

    @permalink
    def get_absolute_url(self):
        return ('project_detail', None, { 'slug': self.slug })

    def set_tags(self, tags):
        Tag.objects.update_tags(self, tags)

    def get_tags(self):
        return Tag.objects.get_for_object(self)

    def save(self, *args, **kwargs):
        """
        Save the object in the database.

        >>> p = Project.objects.create(slug="foo", name="Foo Project",
        ... long_description = '*foo*')
        >>> p.save()
        >>> p.long_description_html
        u'<p><em>foo</em>\\n</p>'
        >>> c = Component(slug='bar', project=p)
        >>> c.save()
        >>> p.num_components
        1
        >>> c.delete()
        >>> p.delete()
        """
        import markdown
        self.date_modified = datetime.now()
        self.long_description_html = markdown.markdown(self.long_description)
        super(Project, self).save(*args, **kwargs)

    def get_langs(self):
        # We can filter for only include languages that have a po file
        # for this module if we want. Now we are showing up all langs.
        return Language.objects.all()
    
    def get_components(self):
        return Component.objects.filter(project=self).order_by('name')
       
    def get_lang_comp_stats(self, lang, component):
        return POStatistic.get_stats_for_lang_object(lang, component)

    def get_stats_dict(self):
        """
        Stats of all components and langs in a dictionary.
        
        Returns a dictionary like:
            {'pt_BR': {'tip': POStatistic objetc,
                       '0.1': POStatistic objetc},
             'el': {'tip': POStatistic objetc,
                    '0.1': POStatistic objetc}
            }
        """
        stats = {}
        for lang in self.get_langs():
            ll = {}
            for comp in self.get_components():
                ll.update({comp: self.get_lang_comp_stats(lang, comp)})
            stats.update({lang: ll})
        return stats



class Component(models.Model):
    """ A component is a translatable resource. """

    slug = models.SlugField()
    project = models.ForeignKey(Project)

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    long_description = models.TextField(blank=True, max_length=1000,
        help_text=_('Use Markdown syntax.'))
    long_description_html = models.TextField(blank=True, null=True,
        max_length=1000, help_text=_('Description as HTML.'), editable=False)
    repository = models.CharField(blank=True, max_length=255,
        help_text=_("The URL of the project's source repository"))
    repository_type = models.CharField(blank=True, max_length=10,
        help_text=_('cvs, svn, hg, git, ...'))
    repository_web = models.CharField(blank=True, null=True, max_length=255,
        help_text=_("A URL to the versioning system's web front-end"))
    branches = models.CharField(blank=True, max_length=255,
        help_text=_('Space-separated list of branch names'))
    report_bugs = models.CharField(blank=True, max_length=255,
        help_text=_("A URL to the project's bugzilla, trac, etc"))

    hidden = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    date_created = models.DateField(default=datetime.now,
                                    editable=False)
    date_modified = models.DateTimeField(editable=False)

    class Meta:
        unique_together = ("project", "slug")
        verbose_name = _('component')
        verbose_name_plural = _('components')
        db_table  = 'projects_component'
        ordering  = ('name',)
        get_latest_by = 'created'

    def __repr__(self):
        return _('<Component: %s>') % self.name
  
    def __unicode__(self):
        return u'%s' % self.name
  
    @permalink
    def get_absolute_url(self):
        return ('component_detail', None,
                { 'project_slug': self.project.slug,
                 'component_slug': self.slug })

    def set_tags(self, tags):
        Tag.objects.update_tags(self, tags)

    def get_tags(self):
        return Tag.objects.get_for_object(self)
    
    tags = property(get_tags, set_tags)

    def save(self, *args, **kwargs):
        import markdown
        self.date_modified = datetime.now()
        self.long_description_html = markdown.markdown(self.long_description)
        super(Component, self).save(*args, **kwargs)

        # Update de-normalized field
        self.project.num_components = self.project.component_set.count()
        self.project.save(*args, **kwargs)
        
    def get_langs(self):
        # We can filter for only include languages that have a po file
        # for this module if we want. Now we are showing up all langs.
        return Language.objects.all()

    def get_lang_stats(self, lang):
        return POStatistic.get_stats_for_lang_object(lang, self)

    def get_all_stats(self):

        # Returns a dictionary like:
        # {'pt_BR': POStatistic objetc},
        #  'el': POStatistic objetc}
        # }

        stats = {}
        for lang in self.get_langs():
            stats.update({lang: self.get_lang_stats(lang)})
        return stats



