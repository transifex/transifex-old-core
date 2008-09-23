import os
from mercurial import ui, hg, commands
from mercurial.repo import RepoError
from vcs.lib import REPOSITORIES_PATH
from vcs.lib.types import (BrowserMixin, BrowserError)


hgrepo_path = os.path.join(REPOSITORIES_PATH, 'hg')

class HgBrowser(BrowserMixin):
    def __init__(self, unit):

        self.unit = unit
        repo_path = os.path.join(hgrepo_path, unit.repository.slug)
        # FIXME: Move to parent
        if not os.path.isdir(repo_path):
            os.mkdir(repo_path)
        self.path = os.path.join(repo_path, unit.slug)

        #mercurial doesn't seem to handle correctly unicode paths
        self.path = str(self.path)

    @property
    def remote_path(self):
        """
        Calculate remote path for cloning
        """
        return str('%s%s' % (self.unit.repository.root, self.unit.directory))

    def init_repo(self):
        """
        Initialize repository for the first time, commands used:

        hg clone <remote_path> <self.path>
        hg update <branch>
        """
        try:
            self.repo = hg.repository(ui.ui(), self.path)
        except RepoError:
            # Repo does not exist, create it"
            try:
                print "Fresh checkout"
                remote_repo, self.repo = hg.clone(ui.ui(), self.remote_path, self.path)
                commands.update(self.repo.ui, self.repo, self.unit.branch)
            except RepoError, e:
                # Remote repo error
                raise BrowserError, e

    def submit(self, files, msg, *args, **kwargs):
        """
        update to upstream
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
            commands.update(self.repo.ui, self.repo, self.unit.branch)
        except RepoError, e:
            raise BrowserError, e
