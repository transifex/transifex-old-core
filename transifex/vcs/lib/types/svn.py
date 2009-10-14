import os
import time
import traceback
import urlparse

import pysvn

from django.conf import settings
from vcs.lib import RepoError
from codebases.lib import BrowserMixin, BrowserError
from txcommon.log import logger

REPO_PATH = settings.REPO_PATHS['svn']
SVN_CREDENTIALS = getattr(settings, 'SVN_CREDENTIALS', {})

def need_repo(fn):
    #This is different than in other vcs systems!
    def repo_fn(self, *args, **kw):
        try:
            self.client.status(self.path)
        except pysvn.ClientError:
            self.init_repo()
        return fn(self, *args, **kw)
    return repo_fn

def need_auth(fn):
    """Decorator for methods needing SVN authentication."""
    def repo_fn(self, *args, **kw):
        if self.root.startswith('https'):
            self._authenticate()
        return fn(self, *args, **kw)
    return repo_fn


def domain_from_hostname(hostname):
    """
    Return the 2nd-level domain from a full hostname.
    
    >>> domain_from_hostname('http://foo.bar.com/')
    'bar.com'
    >>> domain_from_hostname('http://localhost:8000/foo/bar/')
    'localhost'
    """
    urlparser = urlparse.urlsplit(hostname)
    return '.'.join(urlparser.hostname.split('.')[-2:])


class SvnBrowser(BrowserMixin):
    
    """
    A browser class for Subversion repositories.
   
    Subversion homepage: http://subversion.tigris.org/

    >>> b = SvnBrowser(name='test-svn', branch='trunk',
    ... root='http://svn.fedorahosted.org/svn/system-config-language')
    >>> SvnBrowser(root='foo', name='../..', branch='trunk')
    Traceback (most recent call last):
    ...
    AssertionError: Unit checkout path outside of nominal repo checkout path.
    
    """

    # We are using the pysvn module.
    # Pysvn is somewhat different from the mercurial and git apis.
    # We have to specify the full path to svn commands in order to work.

    def __init__(self, root, name=None, branch=None):
        # If name isn't given, let's take the last part of the root
        # Eg. root = 'http://example.com/foo/baz' -> name='baz'
        if not name:
            name = root.split('/')[-1]

        self.root = root
        self.name = name
        self.branch = branch
        
        self.path = os.path.normpath(os.path.join(REPO_PATH, name))
        self.path = os.path.abspath(self.path)
        #Test for possible directory traversal
        assert os.path.commonprefix(
            [self.path, REPO_PATH]) == REPO_PATH, (
            "Unit checkout path outside of nominal repo checkout path.")
        self.client = pysvn.Client()

    def _authenticate(self):
        """
        Authentication for SVN repositories.
        
        Used primarly for https:// repos, which require a username and password
        for write
        operations, taken from the configuration settings.
        """
        domain = domain_from_hostname(self.root)
        credentials = SVN_CREDENTIALS.get(domain, None)
        
        if not credentials:
            msg = "Credentials not found for the domain: %s" % domain
            logger.error(msg)
            raise RepoError(msg)

        self.client.set_auth_cache(False)
        self.client.set_default_username(credentials[0])
        self.client.set_default_password(credentials[1])

    @property
    def remote_path(self):
        """Calculate remote path using the standard svn layout."""
        if self.branch:
            if self.branch == u'trunk':
                repo_path = "%s/trunk" % self.root
            else:
                repo_path = "%s/branches/%s" % (self.root, self.branch)
            return repo_path
        else:
            return self.root


    def setup_repo(self):
        """
        Initialize repository for the first time.
        
        Commands used:
        svn co <remote_path> <self.path>
        """
        #FIXME: This function isn't called by anyone!
        #FIXME: This doesn't look 100% right, but it works and seems to
        # follow pysvn's instructions.
        # Basically we need to call exactly the same commands as the ones
        # we're calling in the following method (client.checkout).
        self.init_repo()


    def init_repo(self):
        """Initialize the ``client`` variable on the browser."""
        try:
            #FIXME: This is simply wrong. Every time we need a browser, we
            # issue a checkout, which is very expensive! This should be done
            # only in setup_repo().
            self.client.checkout(self.remote_path, self.path,
                ignore_externals=True)
        except Exception, e:
            logger.error(traceback.format_exc())
            raise RepoError("Checkout from remote repository failed.")


    def _clean_dir(self):
        """
        Clean the local working directory.
        
        Commands used:
        svn revert -R .
        
        """
        try:
            self.client.revert(self.path, recurse=True)
        except:
            pass

    @need_repo
    def update(self):
        """
        Fully update the local repository.
        
        Commands used:
        clean dir
        svn update
        """
        self._clean_dir()
        self.client.update(self.path)

    @need_repo
    def get_rev(self, obj=None):
        """
        Get the current revision of the repository or a specific
        object.
        
        Commands used:
        svn info
        """
        try:
            if not obj:
                entry = self.client.info(self.path)
            else:
                entry = self.client.info(os.path.join(self.path, obj))
            return (entry.commit_revision.number,)
        # TODO: Make it more specific
        except:
            logger.error(traceback.format_exc())
            raise BrowserError()

    @need_repo
    @need_auth
    def submit(self, files, msg, user):
        """
        svn add <filename>
        svn ci -m <msg> <filename>
        svn update
        """
        # Save contents
        for fieldname, uploadedfile in files.iteritems():
            self.save_file_contents(uploadedfile.targetfile,
                uploadedfile)

        # We have to calculate absolute filenames because of pysvn usage
        absolute_filenames = [os.path.join(self.path, uploadedfile.targetfile)
            for uploadedfile in files.values()]

        # `svn add` untracked files
        for filename in absolute_filenames:
            if not self.client.status(filename)[0]['is_versioned']:
                self.client.add(filename)
        
        try:
            # svn ci files
            self.client.checkin(absolute_filenames, msg.encode('utf-8'))
            self.update()
        except pysvn.ClientError, e:
            # If it's necessary to handle the following pysvn exceptions in 
            # another place as well, it probably worth to move the following 
            # code into a function
            stre = str(e)
            if 'File not found' in stre or 'path not found' in stre:
                msg = "File not found in repo!"
                logger.error(msg)
                raise RepoError(msg)
            elif 'callback_ssl_server_trust_prompt required' in stre:
                home = os.path.expanduser('~')
                msg = ('HTTPS certificate not accepted.  Please ensure that '
                    'the proper certificate exists in %s/.subversion/auth '
                    'for the user that Transifex is running as.' % home)
                logger.error(msg)
                raise RepoError(msg)
            elif 'callback_get_login required' in stre:
                msg = 'Login to the SCM server failed.'
                logger.error(msg)
                raise RepoError(msg)
            else:
                logger.error(traceback.format_exc())
                raise RepoError(stre)
