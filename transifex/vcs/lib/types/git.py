import os
import traceback

from django.conf import settings
from vcs.lib import RepoError
from vcs.lib.types import (VCSBrowserMixin, BrowserError)
from vcs.lib.support.git import repository, clone
from txcommon.log import logger

REPO_PATH = settings.REPO_PATHS['git']

def need_repo(fn):
    def repo_fn(self, *args, **kw):
        try:
            self.repo
        except AttributeError:
            self.init_repo()
        return fn(self, *args, **kw)
    return repo_fn

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


    def __init__(self, root, name=None, branch='master'):
        # If name isn't given, let's take the last part of the root
        # Eg. root = 'http://example.com/foo/baz' -> name='baz'
        if not name:
            name = root.split('/')[-1]

        self.root = root
        self.branch = branch

        self.path = os.path.normpath(os.path.join(REPO_PATH, name))
        self.path = os.path.abspath(self.path)
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
        git clone <remote_path> <self.path>
        if branch != master:
        git branch <branch> <remote_branch>
        git co <branch>
        
        """

        repo = clone(self.remote_path, self.path)

        # Non master branches need more work:
        if self.branch != u'master':
            remote_branch = 'origin/%s' % self.branch
    
            repo.branch(self.branch, remote_branch)
            repo.checkout(self.branch)
        
        return repo


    def init_repo(self):
        """
        Initialize the ``repo`` variable on the browser.
        
        If local repo exists, use that. If not, clone it.
        """
        
        try:
            self.repo = repository(self.path)
        except RepoError:
            self.repo = self.setup_repo()

    def _clean_dir(self):
        """
        Clean the local working directory.
        
        Reset any pending changes.

        Commands used:
        git reset --hard
        """
        try:
            self.repo.reset('--hard')
        except:
            logger.error(traceback.format_exc())
            pass
        
    @need_repo
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

    @need_repo
    def get_rev(self, obj=None):
        """
        Get the current revision of the repository or a specific
        object.
        
        Commands used:
        git show-ref refs/heads/<branch>
        git log -1 --pretty=format:%H <obj>
        """
        try:
            if not obj:
                refspec = 'refs/heads/%s' % self.branch
                rev = self.repo.show_ref(refspec).split()[0]
            else:
                rev = self.repo.log('-1', '--pretty=format:%H', obj)
            return (int(rev, 16),)
        # TODO: Make it more specific
        except:
            logger.error(traceback.format_exc())
            raise BrowserError()

    @need_repo
    def submit(self, files, msg, user):
        self.update()

        for fieldname, uploadedfile in files.iteritems():
            self.save_file_contents(uploadedfile.targetfile,
                uploadedfile)

            self.repo.add(uploadedfile.targetfile)
        
        user = self._get_user(user)

        self.repo.commit(m=msg.encode('utf-8'), 
                         author=user.encode('utf-8'))
        self.repo.push('origin', self.branch)

