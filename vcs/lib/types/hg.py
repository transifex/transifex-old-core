import os
from mercurial import ui, hg, commands
from mercurial.repo import RepoError
from django.conf import settings
from vcs.lib.types import (VCSBrowserMixin, BrowserError)

HG_REPO_PATH = settings.HG_REPO_PATH

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
    
    def __init__(self, root, name, branch):
        import os
        self.root = root
        self.branch = branch
        
        self.path = os.path.normpath(os.path.join(HG_REPO_PATH, name))
        #Mercurial doesn't seem to handle correctly unicode paths
        self.path = str(self.path)
        
        #Test for possible directory traversal
        assert os.path.commonprefix(
            [self.path, HG_REPO_PATH]) == HG_REPO_PATH, (
            "Unit checkout path outside of nominal repo checkout path.")

    @property
    def remote_path(self):
        "Return remote path for cloning."
        return str('%s' % self.root)

    def init_repo(self):
        """
        Initialize repository for the first time.
        
        Commands used:
        hg clone <remote_path> <self.path>
        hg update <branch>
        """
        try:
            self.repo = hg.repository(ui.ui(), self.path)
        except RepoError:
            # Repo does not exist, create it.
            try:
                remote_repo, self.repo = hg.clone(ui.ui(), self.remote_path,
                                                  self.path)
                commands.update(self.repo.ui, self.repo, self.branch)
                self.repo = hg.repository(ui.ui(), self.path)
            except RepoError, e:
                # Remote repo error
                raise BrowserError, e

    def teardown_repo(self):
        """
        Remove the local copy of the repository, ignoring any changes
        that have been made.
        """
        import shutil
        #Fail silently when the repo cannot be destroyed
        try:
            shutil.rmtree(self.path)
        except OSError:
            pass


    def _clean_dir(self):
        """
        hg revert --all --no-backup
        """
        commands.revert(self.repo.ui, self.repo, date=None, rev=None, all=True, no_backup=True)

    def update(self):
        """
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


class HgSubmitter(VCSBrowserMixin):
    """A submit class for Mercurial repositories."""
    
    
    def submit(self, files, msg, *args, **kwargs):
        """
        Update to upstream.
        
        hg commit -m <msg> --addremove
        hg push
        """
        self.update()

        for filename, contents in files.iteritems():
            self.save_file_contents(filename, contents)

        user = '%s <%s>' % (identity.current.user.display_name,
                                   get_user_email(identity))

        commands.commit(self.repo.ui, self.repo, message=self.submit_msg(msg), \
            addremove=True, logfile=None, user=user, date=None)
        commands.push(self.repo.ui, self.repo, force=False, rev=None)

