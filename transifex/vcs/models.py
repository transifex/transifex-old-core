from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from codebases.models import Unit
from txcommon.log import logger

class CheckOutError(Exception):
    pass

def need_browser(fn):
    """Decorator to initialize the vcsunit.browser when it is needed."""

    def browser_fn(self, *args, **kw):
        try:
            self.browser
        except AttributeError:
            self._init_browser()
        return fn(self, *args, **kw)
    return browser_fn


class VcsUnit(Unit):
    """
    A snapshot of a VCS project, an instance of a repository's files.
    
    A vcsunit is a VCS module (component) snapshot, which represents an actual
    directory of files (eg. a repository, branch combination, or a repository, 
    directory, date one). VcsUnits can be checked-out and managed like any real
    set of actual files.
    
    It can be considered as the equivalent of a filesystem's directory.

    >>> u = VcsUnit.objects.create(name="Foo")
    >>> u = VcsUnit.objects.get(name="Foo")
    >>> print u.name
    Foo
    >>> VcsUnit.objects.create( name="Foo")
    Traceback (most recent call last):
        ...
    IntegrityError: column name is not unique
    >>> u.delete()

    """
    
    branch = models.CharField(_('Branch'), max_length=255,
        help_text=_('A VCS branch this unit is associated with'))
    web_frontend = models.CharField(_('Web frontend'), blank=True, null=True, 
        max_length=255,
        help_text=_("A URL to the project's web front-end"))

    unit_types = tuple([x for x in 'bzr', 'cvs', 'git', 'hg', 'svn'
        if x in settings.CODEBASE_CHOICES])

    def __repr__(self):
        return _('<VcsUnit: %(name)s (%(type)s)>') % {'name': self.name,
                                                   'type': self.type}
    class Meta:
        verbose_name = _('vcsunit')
        verbose_name_plural = _('vcsunits')
        ordering  = ('name', 'branch')
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        unit_old = None
        if self.id:
            try:
                unit_old = VcsUnit.objects.get(id=self.id)
            except VcsUnit.DoesNotExist:
                pass

        super(VcsUnit, self).save(*args, **kwargs)

        if unit_old and unit_old.name != self.name:
            unit_old._rename_repo(self.name)

        if unit_old and unit_old.root != self.root:
            self.teardown()

    def delete(self, *args, **kwargs):
        self.teardown()
        super(VcsUnit, self).delete(*args, **kwargs)

    def _init_browser(self):
        """
        Initializes an appropriate VCS browser object, depending
        on the VCS type of the project.
        
        The initialization will raise an exception if the VCS type
        is not specified in the model.
        """  
        from codebases import get_browser_object
        browser = get_browser_object(self.type)
        self.browser = browser(root=self.root,
                               name=self.name,
                               branch=self.branch)

    @need_browser
    def prepare(self):
        """Abstraction for the vcsunit.browser.update."""
        try:
            logger.debug("Preparing repo for vcsunit %s" % self.name)
            self.browser.update()
            self.last_checkout = datetime.now()
            self.save()
        except:
            logger.debug("Repo update failed. Let's clean up and try again.")
            # Try once again with a clean local repo.
            self.teardown()
            self.browser.setup_repo()
            #TODO: Do something if this fails.
            self.browser.update()

    @need_browser
    def get_files(self, file_filter):
        """Abstration for the vcsunit.browser.get_files."""
        return self.browser.get_files(file_filter)

    @need_browser
    def teardown(self):
        """Abstration for the vcsunit.browser.teardown_repo."""
        try:
            logger.debug("Tearing down repo for vcsunit '%s'" % self.name)
            self.browser.teardown_repo()
        except:
            logger.error("Could not teardown repo for vcsunit '%s'" % self.name)
            pass

    @need_browser
    def _rename_repo(self, new_name):
        """Abstration for the vcsunit.browser.rename_repo."""
        logger.debug("Renaming repo of vcsunit '%s' to %s" % (self.name,
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
        
    @classmethod
    def bootstrap_extra(cls, unit):
        unit.branch = ''

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
    from vcs.lib.types import bzr, cvs, git, hg, svn
    s.addTest(doctest.DocTestSuite(bzr))
    s.addTest(doctest.DocTestSuite(cvs))
    s.addTest(doctest.DocTestSuite(git))
    s.addTest(doctest.DocTestSuite(hg))
    s.addTest(doctest.DocTestSuite(svn))
        
    return s
