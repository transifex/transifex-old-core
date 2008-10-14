from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

class CheckOutError(Exception):
    pass

def need_browser(fn):
    """
    Decorator to initialize the unit.browser when it is needed.

    Usage: 
    @need_browser
    def func():
        ...

    """

    def browser_fn(self, *args, **kw):
        try:
            self.browser
        except AttributeError:
            self.init_browser()
        return fn(self, *args, **kw)
    return browser_fn


class Unit(models.Model):
    """
    A snapshot of a VCS project, an instance of a repository's files.
    
    A unit is a VCS module (component) snapshot, which represents an actual
    directory of files (eg. a repository, branch combination, or a repository, 
    directory, date one). Units can be checked-out and managed like any real
    set of actual files.
    
    It can be considered as the equivalent of a filesystem's directory.

    >>> u = Unit.objects.create(name="Foo")
    >>> u = Unit.objects.get(name="Foo")
    >>> print u.name
    Foo
    >>> Unit.objects.create( name="Foo")
    Traceback (most recent call last):
        ...
    IntegrityError: column name is not unique
    >>> u.delete()

    """
    
    name = models.CharField(unique=True, max_length=100)
    root = models.CharField(max_length=255,
        help_text=_("The root URL of the project (without the branch)"))
    type = models.CharField(max_length=10,
                            choices=settings.VCS_CHOICES.items(),
        help_text=_('The repository system type (%s)' %
                    ', '.join(settings.VCS_CHOICES.keys())))
    branch = models.CharField(max_length=255,
        help_text=_('A VCS branch this unit is associated with'))
    web_frontend = models.CharField(blank=True, null=True, max_length=255,
        help_text=_("A URL to the project's web front-end"))

    last_checkout = models.DateTimeField(editable=False, null=True)

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
                               name=self.name,
                               branch=self.branch)
    @need_browser
    def prepare_repo(self):
        """Abstration for the unit.browser.update."""
        try:
            self.browser.update()
            self.last_checkout = datetime.now()
            self.save()
        except:
           raise CheckOutError(_("Could not checkout."))

    @need_browser
    def get_files(self, file_filter):
        """Abstration for the unit.browser.get_files."""
        return self.browser.get_files(file_filter)

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
    from vcs.lib.types import (bzr, git, hg, svn)
    s.addTest(doctest.DocTestSuite(bzr))
    s.addTest(doctest.DocTestSuite(git))
    s.addTest(doctest.DocTestSuite(hg))
    s.addTest(doctest.DocTestSuite(svn))
        
    return s
