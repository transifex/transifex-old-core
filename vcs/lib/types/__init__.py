import os

class BrowserError(Exception):
    pass

class BrowserMixin:
    """
    Implements VCS browser functionality:
    Reading and saving files, creating diffs etc
    """


