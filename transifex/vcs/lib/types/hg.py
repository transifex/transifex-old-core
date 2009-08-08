# -*- coding: utf-8 -*-
import os
import traceback

from mercurial import hg, commands
from vcs.lib.support.hg import ui
try:
    from mercurial.repo import RepoError # mercurial-1.1.x
except:
    from mercurial.error import RepoError # mercurial-1.2.x

from django.conf import settings
from vcs.lib.types import (VCSBrowserMixin, BrowserError)
from txcommon.log import logger

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
    ... name='test-hg', branch='default')
    >>> HgBrowser(root='foo', name='../..', branch='default')
    Traceback (most recent call last):
      ...
    AssertionError: Unit checkout path outside of nominal repo checkout path.
    
    """

   
    def __init__(self, root, name=None, branch='default'):
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
            remote_repo, repo = hg.clone(ui, self.remote_path,
                                         self.path)
            commands.update(repo.ui, repo, self.branch)
            #TODO: Why is the following needed, since it's defined above?
            repo = hg.repository(ui, self.path)
        except RepoError, e:
            # Remote repo error
            logger.error(traceback.format_exc())
            raise BrowserError, e

        return repo


    def init_repo(self):
        """
        Initialize the ``repo`` variable on the browser.
        
        If local repo exists, use that. If not, clone it.
        """
        
        try:
            self.repo = hg.repository(ui, self.path)
        except RepoError:
            self.repo = self.setup_repo()

    def _clean_dir(self):
        """
        Clean the local working directory.
         
        Commands used:
        hg revert --all --no-backup
        hg update -C
        
        """
        try:
            commands.revert(self.repo.ui, self.repo, date=None, rev=None, 
                            all=True, no_backup=True)
            hg.clean(self.repo, self.branch, show_stats=False)
        except:
            pass

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
            logger.error(traceback.format_exc())
            raise BrowserError, e

    @need_repo
    def get_rev(self, obj=None):
        """
        Get the current revision of the repository or a specific
        object.
        """
        try:
            if not obj:
                return (int(self.repo.changectx(self.branch).node().encode('hex'),
                    16),)
            else:
                f = self.repo.changectx(self.branch).filectx(obj)
                return (int(f.filectx(f.filerev()).node().encode('hex'),
                    16),)
        except LookupError, e:
            raise BrowserError(e)

    @need_repo
    def submit(self, files, msg, user):
        """
        update to upstream
        hg commit -m <msg> --addremove
        hg push
        """
        self.update()

        for fieldname, uploadedfile in files.iteritems():
            self.save_file_contents(uploadedfile.targetfile,
                uploadedfile)

        user = self._get_user(user)

        commands.commit(self.repo.ui, self.repo, 
                        message=msg.encode('utf-8'),
                        addremove=True, logfile=None, 
                        user=user.encode('utf-8'),
                        date=None)
        commands.push(self.repo.ui, self.repo, force=False, rev=None)
