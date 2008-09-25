import os
from django.conf import settings

####################
# Methods used for the backend support. Common backend methods go in
# types/.

def get_browser_class(vcs_type):
    """
    Given a vcs type, return the class that provides the browsing
    functionality.
    
    # Get a hardcoded class 
    >>> print get_browser_class('hg')
    vcs.lib.types.hg.HgBrowser
    """
    assert vcs_type in settings.VCS_CHOICES.keys(), (
        "VCS type '%s' is not registered as a supported one." % vcs_type)
      
    return ('%(module)s.%(class)s' % {
        'module': settings.BROWSER_CLASS_BASE,
        'class': settings.BROWSER_CLASS_NAMES[vcs_type]})

def get_browser_object(vcs_type):
    from vcs.lib.common import import_to_python
    return import_to_python(get_browser_class(vcs_type))
