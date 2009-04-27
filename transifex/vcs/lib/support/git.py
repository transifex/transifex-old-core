import os
from vcs.lib import (_Repo, RepoError)
from vcs.lib.support.commands import run_command

"""
Handle low-level bits required by git.
"""


def repository(path=''):
    """Return a repository object for the specified path."""
    return GitRepo(path)


def clone(source, dest, **kw):
    """Clone a git repository and sets it up to track <track> branch."""
    if os.path.exists(dest):
        raise RepoError("destination '%s' already exists" % dest)

    top_dir, git_dir = os.path.split(dest)

    run_command('git clone', source, git_dir, cwd=top_dir, **kw)
    return GitRepo(dest)


def _git_factory(cmd):
    """Create instance wrapper functions for git command <cmd>."""
    def myfunc(self, *args, **kwargs):
        return self.git(cmd, *args, **kwargs)
    return myfunc


class GitRepo(_Repo):

    """
    Handle a local git repo.
    """
    
    CMD = '/usr/bin/env git'

    def git(self, *args, **kwargs):
        """
        Convenience wrapper around ``run``.
        
        Set things up so that commands are run in the canonical
        'git command [options] [args]' form.
        
        """
        cmd = '%s %s' % (GitRepo.CMD, args[0])
        return self.run(cmd, *args[1:], **kwargs)

    add = _git_factory('add')
    branch = _git_factory('branch')
    checkout = _git_factory('checkout')
    reset = _git_factory('reset')
    status = _git_factory('status')
    commit = _git_factory('commit')
    log = _git_factory('log')
    init = _git_factory('init')
    fetch = _git_factory('fetch')
    push = _git_factory('push')
    pull = _git_factory('pull')
    show_ref = _git_factory('show-ref')
