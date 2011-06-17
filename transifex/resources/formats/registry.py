# -*- coding: utf-8 -*-
"""
Register the available formats and their capabilities.
"""

from django.conf import settings
from transifex.txcommon import import_to_python


class _FormatsRegistry(object):
    """Registry class for the formats."""

    def __init__(self, methods=None, handlers=None):
        self.methods = methods or settings.I18N_METHODS
        self.handlers = {}
        handlers = handlers or settings.I18N_HANDLER_CLASS_NAMES
        for method, klass in handlers.iteritems():
            self.handlers[method] = import_to_python(klass)

    def _string_to_list(self, string):
        """
        Convert a string of multiple items separated by commas and spaces
        to a list.
        """
        return string.split(', ')

    def add_handler(self, m, klass, priority=False):
        """Register a new handler for the type m.

        Args:
            m: A i18n_method.
            klass: A handler class for the specified method.
            priority: if this is a priority request, then register the
                 handler for the method anyway. Else, ignore the request.
        Returns:
            True, if the handler was added successfully, False otherwise.
        """
        if m in self.handlers and not priority:
            return False
        self.handlers[m] = klass
        return True

    def extensions_for(self, m):
        """Get the extensions for the specified method.

        Returns:
            A list of file extensions or an empty list,
            in case no such method exists.
        """
        if m not in self.methods:
            return []
        return self._string_to_list(self.methods[m]['file-extensions'])


    def mimetypes_for(self, m):
        """Get the mimetypes for the specified method.

        Args:
            m: The method which we want the mimetypes for.

        Returns:
            The mimetypes for the method or an empty list.
        """
        if m not in self.methods:
            return []
        return self._string_to_list(self.methods[m]['mimetype'])

    def handler_for(self, m):
        """Return a handler for the i18n type specified.

        Args:
            m: A i18n_method

        Returns:
            A particular handler for the method or None, in case the method
            has not been registered.
        """
        if m not in self.handlers:
            return None
        return self.handlers[m]()

registry = _FormatsRegistry()
