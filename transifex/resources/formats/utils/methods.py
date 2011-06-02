# -*- coding: utf-8 -*-

from django.conf import settings


def get_mimetypes_for_method(m):
    """
    Get the mimetype for the specified method.
    """
    if m not in settings.I18N_METHODS:
        return []
    return _string_to_list(settings.I18N_METHODS[m]['mimetype'])


def get_extensions_for_method(m):
    """
    Get a list of extensions for the specified method.

    Returns:
      A list of file extensions or an empty list in case no such method exists.
    """
    if m not in settings.I18N_METHODS:
        return []
    return _string_to_list(settings.I18N_METHODS[m]['file-extensions'])


def get_method_for_mimetype(m):
    """
    Returns the i18n method that corresponds to the supplied mimetype.
    """
    for key in settings.I18N_METHODS:
        if m in get_mimetypes_for_method(key):
            return key
    return None


def _string_to_list(string):
    """
    Convert a string of multiple items separated by commas and spaces to a list.
    """
    return [s.strip() for s in string.split(',')]
