from datetime import datetime
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import permalink
from django.forms import ModelForm
from django.contrib.auth.models import User

from tagging.fields import TagField
from tagging.models import Tag

from translations.models import POStatistic, Language
from vcs.models import Unit

# The following is a tricky module, so we're including it only if needed
if settings.ENABLE_NOTICES:
    from notification import models as notification

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
        # Get a grip on the empty 'created' to detect a new addition. 
        created = self.created
        super(Project, self).save(*args, **kwargs)

        if not created and settings.ENABLE_NOTICES:
            notification.send(User.objects.all(), "projects_added_new",
                              {'project': self})

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

    source_lang = models.CharField(max_length=50,
        help_text=_("The source language for this component, "
                    "eg. 'en', 'pt_BR', 'el'."))
    i18n_type = models.CharField(max_length=20,
        choices=settings.TRANS_CHOICES.items(),
        help_text=_("The code's type of i18n support (%s)" %
                    ', '.join(settings.TRANS_CHOICES.keys())))
    file_filter = models.CharField(max_length=50, blank=True, null=True,
        help_text=_("A regex to filter the exposed files. Eg: 'po/.*'"))

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

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        if self.id:
            self.init_trans()

    def __repr__(self):
        return _('<Component: %s>') % self.name
  
    def __unicode__(self):
        return u'%s' % self.name
  
    @permalink
    def get_absolute_url(self):
        return ('component_detail', None,
                { 'project_slug': self.project.slug,
                 'component_slug': self.slug })
    @property
    def fullname(self):
        return '.'.join([self.project.slug, self.slug])

    def set_tags(self, tags):
        Tag.objects.update_tags(self, tags)

    def get_tags(self):
        return Tag.objects.get_for_object(self)
    
    tags = property(get_tags, set_tags)

    def save(self, *args, **kwargs):
        import markdown
        self.long_description_html = markdown.markdown(self.long_description)
        # Get a grip on the empty 'created' to detect a new addition. 
        created = self.created
        super(Component, self).save(*args, **kwargs)

        # Update de-normalized field
        self.project.num_components = self.project.component_set.count()
        self.project.save(*args, **kwargs)

        if not created and settings.ENABLE_NOTICES:
            notification.send(User.objects.all(), 
                              "projects_added_new_component",  
                              {'project': self.project, 
                              'component': self,})

    def set_unit(self, root, branch, type, web_frontend=None):
        """Associate a unit with this component."""
        if self.unit:
            self.unit.name = self.fullname
            self.unit.root = root
            self.unit.branch = branch
            self.unit.type = type
            self.unit.web_frontend = web_frontend
        else:
            try:
                u = Unit.objects.create(name=self.fullname, root=root, 
                                        branch=branch, type=type, 
                                        web_frontend=web_frontend)
                u.save()
                self.unit = u
            except IntegrityError:
                # TODO: Here we should probably send an e-mail to the 
                # admin, because something very strange would be happening
                pass

    def init_trans(self):
        """ Initialize a TransManager instance for the component. """
        from translations.lib import get_trans_manager
        self.trans = get_trans_manager(self, self.get_files(), 
                                       self.source_lang, self.i18n_type, 
                                       self.unit.browser.path)

    def get_files(self):
        """Return a list of filtered files for the component."""
        self.unit.init_browser()
        return [f for f in self.unit.browser.get_files(self.file_filter)]


    # FIXME: Move this logic inside the POTManager
    def set_stats_for_lang(self, lang):
        """Sets stats for a determinated language."""
        s = self.trans.create_stats(lang)
        s.save()

    def set_stats(self):
        """
        This method is responsable to set up the statistics for a 
        component, calculing the stats for each translation present on it.
        """
        # Initializing the component's unit
        self.unit.init_browser()
        # Unit checkout
        self.unit.browser.init_repo()
        # Deleting all stats for the component
        self.trans.delete_stats_for_object(self)

        for lang in self.trans.get_langs():
            self.set_stats_for_lang(lang)
        
    def get_stats(self):
        return self.trans.get_stats()
