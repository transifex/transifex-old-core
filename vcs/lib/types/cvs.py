import os
import time

from django.conf import settings
from vcs.lib import RepoError
from vcs.lib.types import (VCSBrowserMixin, BrowserError)
from vcs.lib.support.cvs import repository, checkout

REPO_PATH = settings.REPO_PATHS['cvs']

def need_repo(fn):
    def repo_fn(self, *args, **kw):
        try:
            self.client
        except AttributeError:
            self.init_repo()
        return fn(self, *args, **kw)
    return repo_fn

class CvsBrowser(VCSBrowserMixin):
    
    """
    A browser class for CVS repositories.
   
    CVS homepage: http://www.nongnu.org/cvs/

    >>> b = CvsBrowser(root=':pserver:anonymous@cvs.fedoraproject.org:/cvs/elvis',
    ... module='switchdesk')
    >>> print b.module
    switchdesk
    >>> b = CvsBrowser(root=':pserver:anonymous@cvs.fedoraproject.org:/cvs/elvis/switchdesk')
    >>> print b.module
    switchdesk
    >>> b.init_repo()
    >>> b.update()
    >>> CvsBrowser(root='foo', name='../..')
    Traceback (most recent call last):
    ...
    AssertionError: Unit checkout path outside of nominal repo checkout path.
    """

    def __init__(self, root, name=None, branch='HEAD', module=None):
        """
        CVS init's method.
        
        The peculiarity of CVS is that it requires two distinct variables
        to checkout: root and module name. Thus, this method accepts one
        more argument. To keep compatibility with VCSBrowserMixin, this 
        isn't required, and if not given, we assume that root was given
        as root+/+module_name.  
        """

        # Break root
        self.module = root.split('/')[-1] if not module else module
        self.root = '/'.join(root.split('/')[:-1]) if not module else module
        if not name:
            name = self.module
        self.name = name
        self.branch = branch
        
        self.path = os.path.normpath(os.path.join(REPO_PATH, name))
        self.path = os.path.abspath(self.path)        
        #Test for possible directory traversal
        assert os.path.commonprefix(
            [self.path, REPO_PATH]) == REPO_PATH, (
            "Unit checkout path outside of nominal repo checkout path.")


    @property
    def remote_path(self):
        """Return remote path for checkout."""
        return str(self.root)


    def setup_repo(self):
        """
        Initialize repository for the first time.
        
        Commands used:
        cvs -d checkout 
       
        """
        branch = self.branch if self.branch != 'HEAD' else None
        repo = checkout(root=self.root, module=self.module,
                        dest=self.path, branch=branch)
        return repo


    def init_repo(self):
        """
        Initialize the ``repo`` variable on the browser.
        
        If local repo exists, use that. If not, check it out.
        """
        
        try:
            self.repo = repository(self.path)
        except RepoError:
            self.repo = self.setup_repo()

    @need_repo
    def update(self):
        """
        cvs up -PdC
        """
        self.repo.up(P=True, d=True, C=True)
