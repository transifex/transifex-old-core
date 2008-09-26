import os
from django.conf import settings
from vcs.lib import (RepoError, _Repo)
from vcs.lib.types import (VCSBrowserMixin, BrowserError)
from vcs.lib.support.git import repository, clone

GIT_REPO_PATH = settings.GIT_REPO_PATH


class GitBrowser(VCSBrowserMixin):

    """
    A browser class for Git repositories.
    
    Git homepage: http://git.or.cz/

    >>> b = GitBrowser(root='http://git.fedorahosted.org/git/elections.git',
    ... name='test-git', branch='master')
    >>> GitBrowser(root='foo', name='../..', branch='tip')
    Traceback (most recent call last):
      ...
    AssertionError: Unit checkout path outside of nominal repo checkout path.
    
    """

    def __init__(self, root, name, branch):
        self.root = root
        self.branch = branch

        self.path = os.path.normpath(os.path.join(GIT_REPO_PATH, name))
        #Test for possible directory traversal
        assert os.path.commonprefix(
            [self.path, GIT_REPO_PATH]) == GIT_REPO_PATH, (
            "Unit checkout path outside of nominal repo checkout path.")
            
    @property
    def remote_path(self):
        """Return remote path for cloning."""
        return str(self.root)

    def init_repo(self):
        """
        Initialize repository for the first time.
        
        Commands used:
        git clone <remote_path> <self.path>
        if branch != master
            git branch <branch> <remote_branch>
            git co <branch>
        
        """
        try:
            self.repo = clone(self.remote_path, self.path)
        except RepoError:
            pass
        
        if self.branch == u'master':
            return

        # Non master branches
        remote_branch = 'origin/%s' % self.branch
        
        self.repo.branch(self.branch, remote_branch)
        self.repo.checkout(self.branch)

    def update(self):
        """
        Fully update the local repository.
        
        Commands used:
        git fetch origin
        git reset --hard <revspec>
        
        """
        revspec = 'origin/%s' % self.branch
        self.repo.fetch('origin')
        self.repo.reset(revspec, hard=True)
