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

    # Browser initialization
    >>> b = SvnBrowser(name='test-svn', branch='tip',
    ... root='http://svn.fedorahosted.org/svn/system-config-language')

    # Test exception for potential directory traversals.
    >>> SvnBrowser(root='foo', name='../..', branch='trunk')
    Traceback (most recent call last):
        ...
    AssertionError: Unit checkout path outside of nominal repo checkout path.
    
    """

    # We are using the pysvn module.
    # Pysvn is somewhat different from the mercurial and git apis.
    # We have to specify the full path to svn commands in order to work.
 
    def __init__(self, root, name, branch):
        import os
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
        """Initialize repository for the first time.
        
        Commands used:
        svn co <remote_path> <self.path>
        """

        self.client.checkout(self.remote_path, self.path)

    def _clean_dir(self):
        """
        svn revert -R .
        """
        self.client.revert(self.path, recurse=True)

    def update(self):
        """
        clean dir
        svn update
        """
        self._clean_dir()
        self.client.update(self.path)


class SvnSubmitter(VCSBrowserMixin):
    """A submit class for Subversion repositories."""

    def submit_msg(self, msg):
        return cvcs_submit_msg % {
            'message' : msg,
            'date': time.strftime("%Y-%m-%d"),
            'userinfo': get_user_info(),}

    def submit(self, files, msg, *args, **kwargs):
        """
        update
        svn add <filename>
        svn ci
        """
        self.update()

        # Save contents
        for filename, contents in files.iteritems():
            self.save_file_contents(filename, contents)

        # We have to calculate absolute filenames because of pysvn usage
        absolute_filenames = [os.path.join(self.path,filename) \
            for filaname in files.keys()]

        # `svn add` untracked files
        for filename in absolute_filenames:
            if not self.client.status(filename)[0]['is_versioned']:
                self.client.add(filename)
        
        # svn ci files
        self.client.checkin(absolute_filenames, self.submit_msg(msg))
        self.update()