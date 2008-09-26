from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

class Unit(models.Model):
    """
    A snapshot of a VCS project, an instance of a repository's files.
    
    A unit is a VCS module (component) snapshot, which represents an actual
    directory of files (eg. a repository, branch combination, or a repository, 
    directory, date one). Units can be checked-out and managed like any real
    set of actual files.
    
    It can be considered as the equivalent of a filesystem's directory.

    >>> u = Unit.objects.create(slug="foo", name="Foo")
    >>> u = Unit.objects.get(slug='foo')
    >>> print u.name
    Foo
    >>> Unit.objects.create(slug="foo", name="Foo")
    Traceback (most recent call last):
        ...
    IntegrityError: column slug is not unique
    >>> u.delete()

    """
    
    slug = models.SlugField(unique=True)

    name = models.CharField(max_length=50)
    description = models.CharField(blank=True, max_length=255,
        help_text=_("A short description of this object"))

    root = models.CharField(blank=True, max_length=255,
        help_text=_("The root URL of the project (without the branch)"))
    type = models.CharField(blank=True, max_length=10,
                            choices=settings.VCS_CHOICES.items(),
        help_text=_('The repository system type (cvs, hg, git...)'))
    branch = models.CharField(blank=True, max_length=255,
        help_text=_('A VCS branch this unit is associated with'))
    web_frontend = models.CharField(blank=True, null=True, max_length=255,
        help_text=_("A URL to the project's web front-end"))

    hidden = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    date_created = models.DateField(default=datetime.now, editable=False)
    date_modified = models.DateTimeField(editable=False)

    class Meta:
        verbose_name = _('unit')
        verbose_name_plural = _('units')
        db_table  = 'vcs_unit'
        ordering  = ('name',)
        get_latest_by = 'created'

    def __repr__(self):
        return _('<Unit: %s>') % self.name
  
    def __unicode__(self):
        return u'%s' % self.name

    def save(self, *args, **kwargs):
        self.date_modified = datetime.now()
        super(Unit, self).save(*args, **kwargs)

    def init_browser(self):
        """
        Initializes an appropriate VCS browser object, depending
        on the VCS type of the project.
        
        The initialization will raise an exception if the VCS type
        is not specified in the model.
        """   
        from vcs.lib import get_browser_object
        browser = get_browser_object(self.type)
        self.browser = browser(root=self.root,
                               name=self.slug,
                               branch=self.branch)

def suite():
    """
    Define the testing suite for Django's test runner.
    
    Enables test execution with ``./manage.py test <appname>``.
    """
     
    import unittest
    import doctest
    from vcs.lib.common import import_to_python
    s = unittest.TestSuite()

    #FIXME: Load tests automatically:
    #    for vcs_type in settings.VCS_CHOICES:
    #        vcs_browser = import_to_python('vcs.lib.types' % vcs_type)
    #        s.addTest(doctest.DocTestSuite(vcs_browser))
    from vcs.lib.types import (git, hg, svn)
    s.addTest(doctest.DocTestSuite(git))
    s.addTest(doctest.DocTestSuite(hg))
    s.addTest(doctest.DocTestSuite(svn))
        
    return s
