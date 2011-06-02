# -*- coding: utf-8 -*-

from django.conf import settings


def get_extensions_for_method(m):
    """
    Get a list of extensions for the specified method.

    Returns:
      A list of file extensions or an empty list in case no such method exists.
    """
    if m not in settings.I18N_METHODS:
        return []
    return _string_to_list(settings.I18N_METHODS[m]['file-extensions'])


def _string_to_list(string):
    """
    Convert a string of multiple items separated by commas and spaces to a list.
    """
    return [s.strip() for s in string.split(',')]
