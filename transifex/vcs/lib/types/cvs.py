# -*- coding: utf-8 -*-
import os
import time
import traceback
import os.path
from django.conf import settings
from codebases.lib import BrowserMixin, BrowserError
#from vcs.lib import RepoError
from vcs.lib.exceptions import *
from vcs.lib.support.cvs import repository, checkout
from vcs.lib.types import need_repo
from txcommon.commands import CommandError
from txcommon.log import logger

REPO_PATH = settings.REPO_PATHS['cvs']

class CvsBrowser(BrowserMixin):
    
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
        self.module = module
        self.root = module
        if not module:
            self.module = root.split('/')[-1]
            self.root = '/'.join(root.split('/')[:-1])
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
        branch = None
        if self.branch != 'HEAD':
            branch = self.branch
        try:
            self.repo = checkout(root=self.root, module=self.module,
                dest=self.path, branch=branch)
        except Exception, e:
            if hasattr(e, 'stderr'):
                e = e.stderr
            self.teardown_repo()
            raise SetupRepoError(e)

    def init_repo(self):
        """
        Initialize the ``repo`` variable on the browser.

        If local repo exists, use that. If not, check it out.
        """
        try:
            self.repo = repository(self.path)
        except Exception, e:
            if hasattr(e, 'stderr'):
                e = e.stderr
            raise InitRepoError(e)

    @need_repo
    def update(self):
        """
        cvs up -PdC
        """
        try:
            self.repo.up(P=True, d=True, C=True)
        except Exception, e:
            if hasattr(e, 'stderr'):
                e = e.stderr
            raise UpdateRepoError(e)

    def _clean_dir(self):
        """
        Clean the local working directory.
        """
        try:
            self.update()
        except Exception, e:
            if hasattr(e, 'stderr'):
                e = e.stderr
            raise CleanupRepoError(e)

    @need_repo
    def get_rev(self, obj=None):
        """Get the current revision of a file within the repository."""
        try:
            if not obj:
                raise ValueError('CVS repos do not have a global revision')
            p = os.path.join(self.path, obj)
            if not os.path.exists(p):
                raise ValueError('File does not exist in the repository')
            if not os.path.isfile(p):
                raise ValueError('Only files have a revision in CVS')
            d, b = os.path.split(p)
            e = os.path.join(d, 'CVS', 'Entries')
            try:
                ef = open(e, 'r')
                bs = '/%s/' % b
                for line in (entry for entry in ef if entry.startswith(bs)):
                    rev = line.split('/')[2]
                    break
                else:
                    rev = None
                ef.close()
                if rev==None:
                    raise Exception('Could not find a revision')
            except IOError, e:
                raise Exception(str(e))
            return tuple(int(p) for p in rev.split('.'))
        except Exception, e:
            raise RevisionRepoError(e)

    @need_repo
    def submit(self, files, msg, user):
        """
        cvs add <filename>
        cvs commit -m <msg> <filename>
        cvs cvs up -PdC
        """
        # Save contents
        filenames = []
        for fieldname, uploadedfile in files.iteritems():
            filenames.append(uploadedfile.targetfile)
            self.save_file_contents(uploadedfile.targetfile,
                uploadedfile)

        # `cvs add` untracked files
        for uploadedfile in files.values():
            file_status = self.repo.status(uploadedfile.targetfile)
            if file_status.find('Unknown') >= 1:
                self.repo.add(uploadedfile.targetfile)

        files = ' '.join(filenames).encode('utf-8')

        try:
            self.repo.commit(files, m=msg.encode('utf-8'))
        except Exception, e:
            if hasattr(e, 'stderr'):
                e = e.stderr
            raise CommitRepoError(e)

        try:
            self.update()
        except Exception, e:
            if hasattr(e, 'stderr'):
                e = e.stderr
            raise PushRepoError(e)
