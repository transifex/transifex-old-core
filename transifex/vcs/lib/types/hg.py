# -*- coding: utf-8 -*-
import os
import traceback

from mercurial import hg, commands, encoding, cmdutil
from vcs.lib.support.hg import ui
try:
    from mercurial.repo import RepoError # mercurial-1.1.x
except:
    from mercurial.error import RepoError # mercurial-1.2.x

from django.conf import settings
from codebases.lib import BrowserMixin, BrowserError
from vcs.lib.types import need_repo
from txcommon.log import logger

REPO_PATH = settings.REPO_PATHS['hg']

encoding.encoding = 'utf-8'

class HgBrowser(BrowserMixin):

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
            remote_repo, repo = hg.clone(ui, self.remote_path, self.path,
                                         update=True)
        except RepoError, e:
            # Remote repo error
            logger.error(traceback.format_exc())
            raise BrowserError, e

        return (remote_repo, repo)


    def init_repo(self):
        """
        Initialize the ``repo`` variable on the browser.
        
        If local repo exists, use that. If not, clone it.
        """
        
        try:
            self.repo = hg.repository(ui, self.path)
            self.remote_repo = hg.repository(ui, self.remote_path)
        except RepoError:
            self.remote_repo, self.repo = self.setup_repo()

    def _clean_dir(self):
        """
        Clean the local working directory.
         
        Commands used:
        hg update -C
        
        """
        try:
            hg.clean(self.repo, self.branch, show_stats=False)
        except:
            pass

    @need_repo
    def update(self):
        """
        Fully update the local repository.
        
        Commands used:
        hg pull -u
        hg update -C <branch_name>
        
        """
        try:
            commands.pull(self.repo.ui, self.repo, rev=self.branch, force=True) 
            self._clean_dir()
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
            ctx = self.repo[self.branch]
            if obj:
                node = ctx[obj].filenode()
            else:
                node = ctx.node()
            return (int(node.encode('hex'), 16),)
        except LookupError, e:
            raise BrowserError(e)

    @need_repo
    def submit(self, files, msg, user):
        """
        hg commit --addremove -m <msg> --user=<user> <filename>
        hg push
        """
        filenames = []
        for fieldname, uploadedfile in files.iteritems():
            filenames.append(uploadedfile.targetfile)
            self.save_file_contents(uploadedfile.targetfile,
                uploadedfile)

        user = self._get_user(user).encode('utf-8')

        self.repo.add(filenames)

        # Ensure of committing only the right files
        match = cmdutil.match(self.repo, filenames, default=self.path)
        
        self.repo.commit(msg.encode('utf-8'), user=user, match=match)

        commands.push(ui, self.repo, self.root, force=False, revs=self.branch)

