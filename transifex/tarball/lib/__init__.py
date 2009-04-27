import os
from django.conf import settings

####################
# Methods used for the backend support. Common backend methods go in
# types/.

def get_browser_class(codebase_type):
    """
    Return the appropriate VCS browser class.

    Keyword arguments:
    codebase_type -- The type of the codebase, used to decide the class
    to be returned.

    >>> print get_browser_class('hg')
    vcs.lib.types.hg.HgBrowser

    """
    assert codebase_type in settings.CODEBASE_CHOICES, (
        "Codebase type '%s' is not registered as a supported one." %
        codebase_type)

    return settings.BROWSER_CLASS_NAMES[codebase_type]

def get_browser_object(codebase_type):
    """
    Return the appropriate codebase browser object.

    This is a wrapper around get_browser_class which returns
    a browser object, ready to be initialized.

    >>> browser = get_browser_object('hg')

    """

    from txcommon import import_to_python
    return import_to_python(get_browser_class(codebase_type))
