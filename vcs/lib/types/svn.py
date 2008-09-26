import os
import time
import pysvn
from django.conf import settings
from vcs.lib.types import (VCSBrowserMixin, BrowserError)

SVN_REPO_PATH = settings.SVN_REPO_PATH


class SvnBrowser(VCSBrowserMixin):
    
    """
    A browser class for Subversion repositories.
   
    Subversion homepage: http://subversion.tigris.org/

    >>> b = SvnBrowser(name='test-svn', branch='tip',
    ... root='http://svn.fedorahosted.org/svn/system-config-language')
    >>> SvnBrowser(root='foo', name='../..', branch='trunk')
    Traceback (most recent call last):
    ...
    AssertionError: Unit checkout path outside of nominal repo checkout path.
    
    """

    # We are using the pysvn module.
    # Pysvn is somewhat different from the mercurial and git apis.
    # We have to specify the full path to svn commands in order to work.
 
    def __init__(self, root, name, branch):
        self.root = root
        self.name = name
        self.branch = branch
        
        self.path = os.path.normpath(os.path.join(SVN_REPO_PATH, name))
        
        #Test for possible directory traversal
        assert os.path.commonprefix(
            [self.path, SVN_REPO_PATH]) == SVN_REPO_PATH, (
            "Unit checkout path outside of nominal repo checkout path.")
            
        self.client = pysvn.Client()

    @property
    def remote_path(self):
        """Calculate remote path using the standard svn layout."""
        if self.branch == u'trunk':
            repo_path = "%s/trunk" % self.root
        else:
            repo_path += "%s/branches/%" % (self.root, self.branch)
        return repo_path

    def init_repo(self):
        """
        Initialize repository for the first time.
        
        Commands used:
        svn co <remote_path> <self.path>
        
        """

        self.client.checkout(self.remote_path, self.path)

    def _clean_dir(self):
        """
        Clean the local working directory.
        
        Commands used:
        svn revert -R .
        
        """
        self.client.revert(self.path, recurse=True)

    def update(self):
        """
        Fully update the local repository.
        
        Commands used:
        clean dir
        svn update
        """
        self._clean_dir()
        self.client.update(self.path)
