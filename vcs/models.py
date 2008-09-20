from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

class Repository(models.Model):
    """
    A place where content is stored, which can have multiple modules.

    Repositories are primarily identified by their URL, and are used to group
    together modules. Actual file operations can not occur on repositories
    in general, only on their modules.

    >>> Repository.objects.create(slug="foo", name="Foo")
    >>> r = Repository.objects.get(slug='foo')
    >>> print r
    <Repository: Foo>
    >>> Repository.objects.create(slug="foo", name="Foo")
    Traceback (most recent call last):
        ...
    IntegrityError: column slug is not unique
    """
    
    VCS_CHOICES = (
        ('cvs', 'CVS'),
        ('svn', 'Subversion'),
        ('git', 'git'),
        ('hg', 'Mercurial'),
        ('bzr', 'Bazaar'),
    )
    
    slug = models.SlugField(unique=True)

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
      
    root = models.CharField(blank=True, max_length=255,
        help_text=_("The URL of the project's source repository"))
    type = models.CharField(blank=True, max_length=10, choices=VCS_CHOICES,
        help_text=_('The repository system type (cvs, hg, git...)'))
    web_frontend = models.CharField(blank=True, null=True, max_length=255,
        help_text=_("A URL to the repository's web front-end"))

    hidden = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    date_created = models.DateField(default=datetime.now,
                                    editable=False)
    date_modified = models.DateTimeField(editable=False)

    class Meta:
        verbose_name = _('repository')
        verbose_name_plural = _('repositories')
        db_table  = 'vcs_repository'
        ordering  = ('name',)
        get_latest_by = 'created'

    def __repr__(self):
        #TODO: Also return the root here
        return _('<Repository: %(name)s (%(type)s)>') % (self.name, self.type)
  
    def __unicode__(self):
        return u'%s' % self.name

    def save(self):
        self.date_modified = datetime.now()
        super(Repository, self).save()


class Unit(models.Model):
    """
    A snapshot of a VCS project, an instance of a repository's files.
    
    A unit is a VCS module (component) snapshot, which represents an actual
    directory of files (eg. a repository, branch combination, or a repository, 
    directory, date one). Units can be checked-out and managed like any real
    set of actual files.
    
    It can be considered as the equivalent of a filesystem's directory.

    >>> Unit.objects.create(slug="foo", name="Foo")
    >>> u = Unit.objects.get(slug='foo')
    >>> print u
    <Unit: Foo>
    >>> Unit.objects.create(slug="foo", name="Foo")
    Traceback (most recent call last):
        ...
    IntegrityError: column slug is not unique
    """
    
    slug = models.SlugField()
    repository = models.ForeignKey(Repository)

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)

    branch = models.CharField(blank=True, max_length=255,
        help_text=_('A VCS branch this unit is associated with'))
    directory = models.CharField(blank=True, max_length=255,
        help_text=_('The directory that holds the actual set of files'))

    hidden = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    date_created = models.DateField(default=datetime.now,
                                    editable=False)
    date_modified = models.DateTimeField(editable=False)

    class Meta:
        unique_together = ("repository", "slug")
        verbose_name = _('unit')
        verbose_name_plural = _('units')
        db_table  = 'vcs_unit'
        ordering  = ('name',)
        get_latest_by = 'created'

    def __repr__(self):
        return _('<Unit: %(name)s (repo: %(repo)s>') % (
            (self.name, self.repository.name))
  
    def __unicode__(self):
        return u'%s' % self.name

    def save(self):
        self.date_modified = datetime.now()
        super(Unit, self).save()