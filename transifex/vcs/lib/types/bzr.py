import os
import traceback
from bzrlib import bzrdir

try:
    # clean_tree is available on bzr 0.14.x
    from bzrlib import clean_tree
except ImportError:
    # Grab clean_tree from older bzrtools plugin
    from bzrlib.plugins.bzrtools import clean_tree

from bzrlib.errors import NotBranchError

from django.conf import settings
from vcs.lib.types import (VCSBrowserMixin, BrowserError)
from txcommon.log import logger

REPO_PATH = settings.REPO_PATHS['bzr']

def need_repo(fn):
    def repo_fn(self, *args, **kw):
        try:
            self.repo
        except AttributeError:
            self.init_repo()
        return fn(self, *args, **kw)
    return repo_fn

class BzrBrowser(VCSBrowserMixin):

    """
    A browser class for Bazaar repositories.
    
    Bazaar homepage: http://bazaar-vcs.org/

    >>> b = BzrBrowser(
    ... root='http://fedorapeople.org/~wtogami/temp/InstantMirror/',
    ... name='test-bzr')
    >>> BzrBrowser(root='foo', name='../..')
    Traceback (most recent call last):
      ...
    AssertionError: Unit checkout path outside of nominal repo checkout path.
    
    """
    
    def __init__(self, root, name=None, branch=None):
        # If name isn't given, let's take the last part of the root
        # Eg. root = 'http://example.com/foo/baz' -> name='baz'
        if not name:
            name = root.split('/')[-1]

        self.root = root
        self.branch = branch
        self.path = os.path.join(REPO_PATH, name)
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
        Initialize the working tree for the first time.
        
        Commands used:
        bzr checkout --lightweight <remote_path> <self.path>
        """
        remote_work_tree, self.repo = bzrdir.BzrDir.open_tree_or_branch(
            self.remote_path)
        self.work_tree = self.repo.create_checkout(
            self.path, lightweight=True, accelerator_tree=remote_work_tree)


    def init_repo(self):
        """
        Initialize the ``repo`` variable on the browser.
        
        If local repo exists, use that. If not, clone/checkout the repo.
        """
        
        # Transifex only needs the latest workingtree and the ability to make
        # commits.  So a lightweight checkout makes a lot of sense.
        try:
            # Check that the path is a checkout
            self.work_tree, self.repo = bzrdir.BzrDir.open_tree_or_branch(
                self.path)
        except NotBranchError:
            # Else create a lightweight checkout there.
            self.setup_repo()
            
    def _clean_dir(self):
        """
        Clean the local working directory.
        
        Revert any pending changes and all unknown files.

        Commands used:
        bzr revert --no-backup
        bzr clean_tree --ignored --unknown --detritus
        """
        try:
            # Remove any pending changes (left over from a submit that
            # encoutnered an error, for instance).
            self.work_tree.revert(backups=False)
            # Removes all unknown files.  This is important as we don't
            # want to import files that were left over from another run by mistake.
            clean_tree.clean_tree(self.path, unknown=True, ignored=True,
                              detritus=True, no_prompt=True)
        except:
            pass

    @need_repo
    def update(self):
        """
        Fully update the local repository.
        
        Commands used:
        clean dir
        bzr update
        """
        # Note: If we used a branch instead of a checkout, we'd want to use
        # bzr pull.
        self._clean_dir()
        self.work_tree.update()

    @need_repo
    def get_rev(self, obj=None):
        """
        Get the current revision of the repository or a specific
        object.
        """
        try:
            if not obj:
                return self.repo.last_revision_info()[0:1]
            else:
                m = self.repo.get_revision_id_to_revno_map()
                t = self.repo.repository.revision_tree(
                    self.repo.last_revision())
                i = t.inventory[t.path2id(obj)]
                return m[i.revision]
        # TODO: Make it more specific
        except:
            logger.error(traceback.format_exc())
            raise BrowserError()

    @need_repo
    def submit(self, files, msg, user):
        """
        update to upstream
        bzr add <filename>
        bzr commit -m <msg>
        # Lightweight checkout so no push is needed
        """
        self.update()

        for fieldname, uploadedfile in files.iteritems():
            self.save_file_contents(uploadedfile.targetfile,
                uploadedfile)

        # smart_add recursively checks all files in the tree
        self.work_tree.smart_add([self.path])
        user = self._get_user(user)

        self.work_tree.commit(message=msg.encode('utf-8'),
                revprops={'author': user.encode('utf-8')})
