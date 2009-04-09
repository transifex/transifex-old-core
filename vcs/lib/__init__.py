import os
from django.conf import settings
from vcs.lib.support.commands import run_command

class RepoError(Exception):
    pass

class _Repo(object):
    def __init__(self, path):
        self.path = os.path.realpath(path)

        if not os.path.isdir(self.path) or not os.path.exists(self.path):
            raise RepoError("repository %s not found" % self.path)

    def run(self, *args, **kwargs):
        return run_command(cwd=self.path, *args, **kwargs)


####################
# Methods used for the backend support. Common backend methods go in
# types/.

def get_browser_class(vcs_type):
    """
    Return the appropriate VCS browser class.

    Keyword arguments:
    vcs type -- The type of the VCS, used to decide the class to be
    returned.

    >>> print get_browser_class('hg')
    vcs.lib.types.hg.HgBrowser

    """
    assert vcs_type in settings.CODEBASE_CHOICES.keys(), (
        "VCS type '%s' is not registered as a supported one." % vcs_type)

    return settings.BROWSER_CLASS_NAMES[vcs_type]

def get_browser_object(vcs_type):
    """
    Return the appropriate VCS browser object.

    This is a wrapper around get_browser_class which returns
    a browser object, ready to be initialized.

    >>> browser = get_browser_object('hg')

    """

    from vcs.lib.common import import_to_python
    return import_to_python(get_browser_class(vcs_type))
