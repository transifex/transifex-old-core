from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from txcommon.log import logger

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
    last_checkout = models.DateTimeField(null=True, editable=False,
        help_text=_("The last time this unit was checked-out from its repo."))

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __repr__(self):
        return _('<Unit: %(name)s (%(type)s)>') % {'name': self.name,
                                                   'type': self.type}

    class Meta:
        verbose_name = _('unit')
        verbose_name_plural = _('units')
        db_table  = 'vcs_unit'
        ordering  = ('name', 'branch')
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        if self.id:
            unit_old = Unit.objects.get(id=self.id)
        else:
            unit_old = None

        super(Unit, self).save(*args, **kwargs)

        if unit_old and unit_old.name != self.name:
            unit_old.rename_repo(self.name)

    def delete(self, *args, **kwargs):
        self.teardown_repo()
        super(Unit, self).delete(*args, **kwargs)

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
            logger.debug("Preparing repo for unit %s" % self.name)
            self.browser.update()
            self.last_checkout = datetime.now()
            self.save()
        except:
            logger.debug("Repo update failed. Let's clean up and try again.")
            # Try once again with a clean local repo.
            self.teardown_repo()
            self.browser.setup_repo()
            #TODO: Do something if this fails.
            self.browser.update()

    @need_browser
    def get_files(self, file_filter):
        """Abstration for the unit.browser.get_files."""
        return self.browser.get_files(file_filter)

    def teardown_repo(self):
        """Abstration for the unit.browser.teardown_repo."""
        try:
            logger.debug("Tearing down repo for unit '%s'" % self.name)
            self.browser.teardown_repo()
        except:
           logger.error("Could not teardown repo for unit '%s'" % self.name)
           pass

    @need_browser
    def rename_repo(self, new_name):
        """Abstration for the unit.browser.rename_repo."""
        logger.debug("Renaming repo of unit '%s' to %s" % (self.name,
                                                           new_name))
        self.browser.rename_repo(new_name)

    @need_browser
    def get_rev(self, path=None):
        """Get revision of a path from the underlying VCS"""
        return self.browser.get_rev(path)

    @need_browser
    def submit(self, files, msg, user):
        """Get revision of a path from the underlying VCS"""
        return self.browser.submit(files, msg, user)
        
def suite():
    """
    Define the testing suite for Django's test runner.
    
    Enables test execution with ``./manage.py test <appname>``.
    """
     
    import unittest
    import doctest
    s = unittest.TestSuite()

    #FIXME: Load tests automatically:
    #    for vcs_type in settings.VCS_CHOICES:
    #        vcs_browser = import_to_python('vcs.lib.types' % vcs_type)
    #        s.addTest(doctest.DocTestSuite(vcs_browser))
    from vcs.lib.types import (bzr, cvs, git, hg, svn)
    s.addTest(doctest.DocTestSuite(bzr))
    s.addTest(doctest.DocTestSuite(cvs))
    s.addTest(doctest.DocTestSuite(git))
    s.addTest(doctest.DocTestSuite(hg))
    s.addTest(doctest.DocTestSuite(svn))
        
    return s
