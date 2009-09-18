from django.conf import settings

class CodebaseError(StandardError):
    pass

def need_browser(fn):
    """Decorator to initialize the unit.browser when it is needed."""

    def browser_fn(self, *args, **kw):
        if not (hasattr(self, 'browser') and self.browser):
            self._init_browser()
        return fn(self, *args, **kw)
    return browser_fn

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
