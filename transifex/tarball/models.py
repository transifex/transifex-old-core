"""
This module contains a model that is expected to be used for the
codebases used by Transifex. The following definitions are used:

resource:
  A file within a codebase
codebase:
  A collection of files (VCS repo, tarball, etc.) that contains
  resources, some or all of which are to be translated
"""
from datetime import datetime

from django.utils.translation import ugettext_lazy as _

from codebases import need_browser
from codebases.models import Unit
from txcommon.log import logger

class Tarball(Unit):
    '''
    A tarball found on a remote server. It is controlled locally via
    a mercurial repo.
    '''
#    checksum = CharField('Checksum of the downloaded tarball',
#        max_length=128)

    unit_types = ('tar',)

    def __repr__(self):
        return '<Tarball: %(name)s)>' % {'name': self.name}

    class Meta:
        verbose_name = _('tarball')
        verbose_name_plural = _('tarballs')
        ordering  = ('name',)
        get_latest_by = 'created'

    def __init__(self, *args, **kwargs):
        self.codebase = None
        super(Tarball, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        unit_old = None
        try:
            unit_old = type(self).objects.get(id=self.id)
        except type(self).DoesNotExist:
            pass

        Unit.save(self, *args, **kwargs)

        if unit_old and unit_old.name != self.name:
            unit_old._rename_repo(self.name)

    def delete(self, *args, **kwargs):
        self.teardown()
        Unit.delete(self, *args, **kwargs)

    def _init_browser(self):
        """
        Initializes an appropriate codebase browser object, depending
        on the type of the project.
        
        The initialization will raise an exception if the type
        is not specified in the model.
        """  
        from tarball.lib import get_browser_object
        browser = get_browser_object(self.type)
        self.browser = browser(root=self.root,
                               name=self.name)

    @need_browser
    def prepare(self):
        """Abstraction for the tarball.browser.update."""
        try:
            logger.debug("Preparing repo for tarball %s" % self.name)
            self.browser.update()
            self.last_checkout = datetime.now()
            self.save()
        except:
            logger.debug("Tarball update failed. Let's clean up and try again.")
            # Try once again with a clean local repo.
            self.teardown()
            self.browser.setup_codebase()

    @need_browser
    def get_files(self, file_filter):
        """Abstration for the tarball.browser.get_files."""
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
