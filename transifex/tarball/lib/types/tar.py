# -*- coding: utf-8 -*-
import os, os.path
import sys
import tarfile
import traceback

import urlgrabber
from mercurial import hg, commands
try:
    from mercurial.repo import RepoError # mercurial-1.1.x
except ImportError:
    from mercurial.error import RepoError # mercurial-1.2.x

import settings
from txcommon import version
from txcommon.log import logger
from codebases.lib import BrowserMixin, BrowserError
from tarball.lib.types import need_codebase
from vcs.lib.support.hg import ui

class TarballBrowser(BrowserMixin):
    '''
    A browser class for tarballs
    '''

    def __init__(self, root, name=None):
        # If name isn't given, let's take the last part of the root
        # Eg. root = 'http://example.com/foo/baz' -> name='baz'
        if not name:
            name = root.split('/')[-1]

        self.codebase = None

        self.name = name
        
        codebase_path = settings.REPO_PATHS['tar']
        
        self.root = root
        self.branch = 'default'
        
        self.base_path = os.path.normpath(os.path.join(
            codebase_path, name))
        self.base_path = os.path.abspath(self.base_path)
        self.base_path = str(self.base_path)
        #Test for possible directory traversal
        assert os.path.commonprefix(
            [self.base_path, codebase_path]) == codebase_path, (
            "Unit checkout path outside of nominal repo checkout path.")

        #The self.path must be where the files from the VCS can actually be found
        self.path = os.path.join(self.base_path, 'extract')

    def _download(self, url, filename):
        try:
            urlgrabber.urlgrab(url, filename, timeout=15,
                user_agent=('Transifex/%s' % version))
        except urlgrabber.grabber.URLGrabError, e:
            raise BrowserError(e)

    def _extract(self, filename, path):
        try:
            tarball = tarfile.open(filename, 'r')
            try:
                for info in tarball:
                    if (info.name.startswith('../') or
                        info.name.startswith('/') or
                        ('/../' in info.name)):
                        raise BrowserError('Exploitive tarball found: '
                            '%s' % filename)
                    tarball.extract(info, path)
            finally:
                tarball.close()
        except tarfile.ReadError:
            logger.error(traceback.format_exc())
            raise BrowserError('Invalid or corrupt tarball: %s' %
                filename)

    @property
    def remote_path(self):
        """Return remote path for cloning."""
        return str(self.root)

    def setup_codebase(self):
        '''
        Download and extract tarball
        '''
        def clean_mkdir(path):
            try:
                os.makedirs(path)
            except OSError, e:
                if e.errno == 17:
                    if os.path.isdir(path):
                        return
                logger.error(traceback.format_exc())
                raise BrowserError(e)

        download = os.path.join(self.base_path, 'download')
        filename = os.path.join(download, self.name)
        extract = self.path

        clean_mkdir(download)
        clean_mkdir(extract)

        self._download(self.remote_path, filename)
        self._extract(filename, extract)
        
        commands.init(ui, extract)
        repo = hg.repository(ui, extract)
        commands.commit(ui, repo, 
                        message='Initial codebase',
                        addremove=True, logfile=None, 
                        user=('Transifex/%s' % version),
                        date=None)

        try:
            return repo
        except RepoError, e:
            logger.error(traceback.format_exc())
            raise BrowserError(e)

    def init_codebase(self):
        '''
        Set the codebase attribute if the codebase has been setup
        Otherwise, set it up
        ''' 
        try:
            self.codebase = hg.repository(ui, self.path)
        except RepoError:
            self.codebase = self.setup_codebase()

    @need_codebase
    def get_rev(self, obj=None):
        '''
        Get the current revision of the repository or a specific
        object
        '''
        try:
            if not obj:
                return (int(self.codebase.changectx(self.branch).node().
                    encode('hex'), 16),)
            else:
                f = self.codebase.changectx(self.branch).filectx(obj)
                return (int(f.filectx(f.filerev()).node().encode('hex'),
                    16),)
        except LookupError, e:
            logger.error(traceback.format_exc())
            raise BrowserError(e)

    @need_codebase
    def submit(self, files, msg, user):
        '''
        Update files locally
        '''
        for fieldname, uploadedfile in files.iteritems():
            self.save_file_contents(uploadedfile.targetfile,
                uploadedfile)

        user = self._get_user(user)

        commands.commit(self.codebase.ui, self.codebase, 
                        message=msg.encode('utf-8'),
                        addremove=True, logfile=None, 
                        user=user.encode('utf-8'),
                        date=None)

    @need_codebase
    def update(self):
        try:
            hg.repository(ui, self.path)
        except RepoError:
            logger.error(traceback.format_exc())
            self.init_codebase()
