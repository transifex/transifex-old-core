import os

from mercurial import ui, hg, commands
from mercurial.repo import RepoError

from django.conf import settings
from vcs.lib.types import (VCSBrowserMixin, BrowserError)

REPO_PATH = settings.REPO_PATHS['hg']

def need_repo(fn):
    def repo_fn(self, *args, **kw):
        try:
            self.repo
        except AttributeError:
            self.init_repo()
        return fn(self, *args, **kw)
    return repo_fn

class HgBrowser(VCSBrowserMixin):

    """
    A browser class for Mercurial repositories.
    
    Mercurial homepage: http://www.selenic.com/mercurial/

    >>> b = HgBrowser(root='http://code.transifex.org/transifex',
    ... name='test-hg', branch='tip')
    >>> HgBrowser(root='foo', name='../..', branch='tip')
    Traceback (most recent call last):
      ...
    AssertionError: Unit checkout path outside of nominal repo checkout path.
    
    """

   
    def __init__(self, root, name=None, branch='tip'):
        # If name isn't given, let's take the last part of the root
        # Eg. root = 'http://example.com/foo/baz' -> name='baz'
        if not name:
            name = root.split('/')[-1]
        
        self.root = root
        self.branch = branch
        
        self.path = os.path.normpath(os.path.join(REPO_PATH, name))
        self.path = os.path.abspath(self.path)
        #Mercurial doesn't seem to handle correctly unicode paths
        self.path = str(self.path)
        #Test for possible directory traversal
        assert os.path.commonprefix(
            [self.path, REPO_PATH]) == REPO_PATH, (
            "Unit checkout path outside of nominal repo checkout path.")


    @property
    def remote_path(self):
        """Return remote path for cloning."""
        return str(self.root)


    def setup_repo(self):
        """
        Initialize repository for the first time.
        
        Commands used:
        hg clone <remote_path> <self.path>
        hg update <branch>
        
        """

        try:
            remote_repo, repo = hg.clone(ui.ui(), self.remote_path,
                                         self.path)
            commands.update(repo.ui, repo, self.branch)
            #TODO: Why is the following needed, since it's defined above?
            repo = hg.repository(ui.ui(), self.path)
        except RepoError, e:
            # Remote repo error
            raise BrowserError, e

        return repo


    def init_repo(self):
        """
        Initialize the ``repo`` variable on the browser.
        
        If local repo exists, use that. If not, clone it.
        """
        
        try:
            self.repo = hg.repository(ui.ui(), self.path)
        except RepoError:
            self.repo = self.setup_repo()


    def _clean_dir(self):
        """
        Clean the local working directory.
         
        Commands used:
        hg revert --all --no-backup
        
        """
        commands.revert(self.repo.ui, self.repo, date=None, rev=None, all=True, no_backup=True)

    @need_repo
    def update(self):
        """
        Fully update the local repository.
        
        Commands used:
        clean dir
        hg pull -u
        hg update <branch_name>
        
        """
        try:
            self._clean_dir()
            commands.pull(self.repo.ui, self.repo, rev=None, force=False, update=True)
            commands.update(self.repo.ui, self.repo, self.branch)
        except RepoError, e:
            raise BrowserError, e

    @need_repo
    def get_rev(self, obj=None):
        """
        Get the current revision of the repository or a specific
        object.
        """
        if not obj:
            return (int(self.repo.changectx(self.branch).node().encode('hex'),
                16),)
        else:
            f = self.repo.changectx(self.branch).filectx('NOTES')
            return (int(f.filectx(f.filerev()).node().encode('hex'),
                16),)
