import datetime

from django.contrib import admin
from django.db import models
from django.db.models import permalink
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

import tagging
from tagging.fields import TagField
from tagging.models import Tag

class StatsRow():
    def __init__(self):
        from random import randint
        self.total = 30*randint(1, 100)
        self.trans = randint(0, self.total)
        self.fuzzy = randint(0, self.total - self.trans)
        self.untrans = self.total - self.trans - self.fuzzy

        #self.total = 100
        #self.trans = 50
        #self.fuzzy = 30
        #self.untrans = 20

    @property
    def trans(self):
        return self.trans

    @property
    def fuzzy(self):
        return self.fuzzy

    @property
    def untrans(self):
        return self.untrans

    @property
    def total(self):
        return self.total

    @property
    def trans_perc(self):
        return self.trans*100/self.total

    @property
    def fuzzy_perc(self):
        return self.fuzzy*100/self.total

    @property
    def untrans_perc(self):
        return self.untrans*100/self.total

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
    """

    name = models.CharField(blank=False, null=False, max_length=50)
    description = models.CharField(max_length=255)
    long_description = models.TextField(blank=True, max_length=1000,
        help_text=_('Use Markdown syntax.'))
    long_description_html = models.TextField(blank=True, max_length=1000, 
        help_text=_('Description as HTML.'), editable=False)
    slug = models.SlugField(unique=True)
    
    num_components = models.PositiveIntegerField(editable=False, default=0)

    homepage = models.CharField(blank=True, max_length=255)
    feed = models.CharField(blank=True, max_length=255,
        help_text=_('An RSS feed with updates on the project.'))
    enabled = models.BooleanField(default=True)
    created = models.DateField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    #tags = TagField(help_text="Separate tags with spaces.", blank=True, null=True)

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

        >>> p = Project.objects.get(slug='foo')
        >>> p.long_description = '*foo*'
        >>> p.save()
        >>> p.long_description_html
        u'<p><em>foo</em>\\n</p>'
        >>> c = Component(slug='bar', project=p)
        >>> c.save()
        >>> p.num_components
        1
        """
        import markdown
        self.date_modified = datetime.datetime.now()
        self.long_description_html = markdown.markdown(self.long_description)
        super(Project, self).save(*args, **kwargs)

    def get_langs(self):
        return sorted(['pt_BR', 'el', 'es', 'sr', 'ca', 'hu', 'ja', 'pt', 'de'])
    
    def get_components(self):
        return ['tip','0.4.x',  '0.3.2.x', '0.3', '0.2', '0.1']

    def get_lang_comp_stats(self, lang, component):
        return StatsRow()

    def get_stats(self):

        # Stats of all components and langs.
        #
        # Returns a dictionary like:
        # {'pt_BR': {'tip': StatsRow objetc,
        #            '0.1': StatsRow objetc},
        #  'el': {'tip': StatsRow objetc,
        #         '0.1': StatsRow objetc}
        # }

        stats = {}
        for lang in self.get_langs():
            ll = {}
            for comp in self.get_components():
                ll.update({comp: self.get_lang_comp_stats(lang, comp)})
            stats.update({lang: ll})
        return stats

# Tagging
#tagging.register(Project)

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
        help_text=_('Use Markdown syntax.'))
    long_description_html = models.TextField(blank=True, null=True,
        max_length=1000, help_text=_('Description as HTML.'), editable=False)
    slug = models.SlugField()
    
    project = models.ForeignKey(Project)
      
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
    enabled = models.BooleanField(default=True)
    date_created = models.DateField(default=datetime.datetime.now,
                                    editable=False)
    date_modified = models.DateTimeField(editable=False)

    #tags = TagField(help_text="Separate tags with spaces.")

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

    def save(self):
        import markdown
        self.date_modified = datetime.datetime.now()
        self.long_description_html = markdown.markdown(self.long_description)
        super(Component, self).save()
        # Update de-normalized field
        self.project.num_components = self.project.component_set.count()
        #self.project.component_set.add(self)
        self.project.save()

    def get_langs(self):
        return sorted(['pt_BR', 'el', 'es', 'sr', 'ca', 'hu', 'ja', 'pt', 'de'])

    def get_lang_stats(self, lang):
        return StatsRow()

    def get_all_stats(self):

        # Returns a dictionary like:
        # {'pt_BR': StatsRow objetc},
        #  'el': StatsRow objetc}
        # }

        stats = {}
        for lang in self.get_langs():
            stats.update({lang: self.get_lang_stats(lang)})
        return stats



class ComponentAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
admin.site.register(Component, ComponentAdmin)
