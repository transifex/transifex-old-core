import os
from vcs.lib import (_Repo, RepoError)
from vcs.lib.support.commands import run_command

def repository(path):
    """
    Returns a repository object for the specified path.
    """
    return CvsRepo(path)

def checkout(root, module, dest, branch=None, **kw):
    """
    Checks out a cvs repository and sets it up.
    """
    if os.path.exists(dest):
        raise RepoError("destination '%s' already exists" % dest)

    top_dir, cvs_dir = os.path.split(dest)
    cmd = "cvs -d%s co" % root
    if not branch:
        run_command(cmd, module, d=cvs_dir, cwd=top_dir, **kw)
    else:
        run_command(cmd, module, branch, d=cvs_dir, cwd=top_dir, **kw)
    return CvsRepo(dest)

def _cvs_factory(cmd):
    """
    Creates instance wrapper functions for cvs command <cmd>.
    """
    def myfunc(self, *args, **kwargs):
        return self.cvs(cmd, *args, **kwargs)
    return myfunc

class CvsRepo(_Repo):
    """
    Handles a local cvs repo.
    """
    CMD = '/usr/bin/env cvs'
    COMPRESSION = '-z4'
    def cvs(self, *args, **kwargs):
        """This is a convenience wrapper around run that
        sets things up so that commands are run in the canonical
        'cvs command [options] [args]' form."""
        cmd = '%s %s %s' % (CvsRepo.CMD, self.COMPRESSION, args[0])
        return self.run(cmd, *args[1:], **kwargs)

    add = _cvs_factory('add')
    commit = _cvs_factory('commit')
    status = _cvs_factory('status')
    up = _cvs_factory('up')

