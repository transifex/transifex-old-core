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
            self.setup_repo()
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
    if isinstance(urlparser, tuple):
        return '.'.join(urlparser[1].split('.')[-2:])
    return '.'.join(urlparser.hostname.split('.')[-2:])


def _exception_handler(e, default_message=None):
    """
    Take an exception output, usually from the pysvn client, and split it into 
    some more detailed exceptions, if possible.
    
    Parameters:
    ``e`` is a exception object
    ``default_message`` is the message to be displayed case the handler can not
    split the exception into something more specific. If no message is passed
    the exception output will be used.
    """
    stre = str(e)
    if 'File not found' in stre or 'path not found' in stre:
        msg = "File not found in repo!"
        logger.error(msg)
        raise RepoError(msg)
    elif 'callback_ssl_server_trust_prompt required' in stre:
        home = os.path.expanduser('~')
        msg = ('HTTPS certificate not accepted. Please ensure that '
            'the proper certificate exists in %s/.subversion/auth '
            'for the user that Transifex is running as.' % home)
        logger.error(msg)
        raise RepoError('HTTPS certificate not accepted.')
    elif 'callback_get_login required' in stre:
        msg = 'Login to the SCM server failed.'
        logger.error(msg)
        raise RepoError(msg)
    else:
        logger.error(traceback.format_exc())
        raise RepoError(default_message or stre)

class SvnBrowser(BrowserMixin):
    
    """
    A browser class for Subversion repositories.
    
    Note, that compared to the other Browsers, this one is stateless: It
    doesn't require a self.repo object or something, since each command
    can execute without any preparation. For this reason, init_repo is
    not doing much.
   
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

        # Handle SSL warnings
        def _ssl_server_trust_prompt(trust_data):
            return True, trust_data['failures'], True

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
        self.client.callback_ssl_server_trust_prompt = _ssl_server_trust_prompt
        
    def _authenticate(self):
        """
        Authentication for SVN repositories.
        
        Used primarly for https:// repos, which require a username and password
        for write
        operations, taken from the configuration settings.
        """
        domain = domain_from_hostname(self.root)
        username, passwd = SVN_CREDENTIALS.get(domain, (None, None))

        self.client.set_auth_cache(False)
        self.client.set_default_username(username)
        self.client.set_default_password(passwd)

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


    @need_auth
    def setup_repo(self):
        """
        Initialize repository for the first time.
        
        Commands used:
        svn co <remote_path> <self.path>
        """
        try:
            self.client.checkout(self.remote_path, self.path,
                ignore_externals=True)
        except Exception, e:
            _exception_handler(e, "Checkout from remote repository failed.")


    @need_auth
    def init_repo(self):
        """
        A browser repo initialization method, for compatibility reasons.
        
        pysvn runs commands in a stateless fashion, so we don't require an
        initialization phase. The local repo existence check is handled by
        the ``need_repo`` decorator.
        """
        pass


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

        # Get username from User or Profile, depending on the type of instance 
        # that the parameter 'user' is.
        username = getattr(user, 'username', user.user.username)

        try:
            # svn ci files
            r = self.client.checkin(absolute_filenames, msg.encode('utf-8'))

            try:
                # Set the author property for the revision
                self.client.revpropset("svn:author", username, self.root, r)
            except pysvn.ClientError, e:
                logger.info("Could not set author property for a svn commit:\n"
                    "%s" % str(e))

            self.update()
        except pysvn.ClientError, e:
            _exception_handler(e)
