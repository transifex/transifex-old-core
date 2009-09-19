import os
from txcommon.commands import run_command

class RepoError(Exception):
    pass

class _Repo(object):
    def __init__(self, path):
        self.path = os.path.realpath(path)

        if not os.path.isdir(self.path) or not os.path.exists(self.path):
            raise RepoError("repository %s not found" % self.path)

    def run(self, *args, **kwargs):
        return run_command(cwd=self.path, *args, **kwargs)
