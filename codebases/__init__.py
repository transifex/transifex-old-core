class CodebaseError(StandardError):
    pass

def need_browser(fn):
    """Decorator to initialize the unit.browser when it is needed."""

    def browser_fn(self, *args, **kw):
        if not (hasattr(self, 'browser') and self.browser):
            self._init_browser()
        return fn(self, *args, **kw)
    return browser_fn
