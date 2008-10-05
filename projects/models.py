from datetime import datetime
from django.conf import settings
from django.db import models
from django.db.models import permalink
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField
from tagging.models import Tag

from statistics.models import POStatistic, Language
from vcs.models import Unit

if settings.ENABLE_NOTICES:
    from notification import models as notification
    from django.contrib.auth.models import User
else:
    notification = None

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

    hidden = models.BooleanField(default=False,
        help_text=_('Hide this object from the list view?'))
    enabled = models.BooleanField(default=True,
        help_text=_('Enable this object or disable its use?'))
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
        created = self.created
        super(Project, self).save(*args, **kwargs)

        if not created and notification:
            notification.send(User.objects.all(), "projects_added_new",
                              {'project': self})

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
            {'pt_BR': {'tip': POStatistic object,
                       '0.1': POStatistic object},
             'el': {'tip': POStatistic object,
                    '0.1': POStatistic object}
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
    unit = models.ForeignKey(Unit, blank=True, null=True, editable=False)

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    long_description = models.TextField(blank=True, max_length=1000,
        help_text=_('Use Markdown syntax.'))
    long_description_html = models.TextField(blank=True, null=True,
        max_length=1000, help_text=_('Description as HTML.'), editable=False)

    hidden = models.BooleanField(default=False,
        help_text=_('Hide this object from the list view?'))
    enabled = models.BooleanField(default=True,
        help_text=_('Enable this object or disable its use?'))
    created = models.DateField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

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
        self.long_description_html = markdown.markdown(self.long_description)
        created = self.created
        super(Component, self).save(*args, **kwargs)

        # Update de-normalized field
        self.project.num_components = self.project.component_set.count()
        self.project.save(*args, **kwargs)

        if not created and notification:
            notification.send(User.objects.all(), 
                              "projects_added_new_component",  
                              {'project': self.project, 
                              'component': self,})
        
    def get_langs(self):
        # We can filter for only include languages that have a po file
        # for this module if we want. Now we are showing up all langs.
        return Language.objects.all()

    def get_lang_stats(self, lang):
        return POStatistic.get_stats_for_lang_object(lang, self)

    def get_all_stats(self):
        # Returns a list like:
        # [POStatistic object,
        #  POStatistic object]
        return POStatistic.get_stats_for_object(self)
