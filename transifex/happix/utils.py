# -*- coding: utf-8 -*-
"""
Utility methods used for happix core functionality
"""
import os, re, settings


# ./codebases/lib/__init__.py
def valid_filename(filename, filefilter=None):
    """
    Check if it has access to a filename checking against the 
    ``IGNORE_WILDCARD_LIST`` in settings and a ``filefilter``, if passed by
    parameter.

    Return a boolean value

    """
    filter_check = True
    if filefilter and not re.compile(filefilter).match(filename):
        filter_check = False

    return not re.compile(settings.IGNORE_WILDCARD_LIST).match(
        '/%s' % filename) and filter_check


# ./codebases/lib/__init__.py
def get_files(path, filefilter=None):
    """
    Yield files for the filesystem

    It can be used with a ``filefilter`` parameter to filter the
    output result to avoid to get all files.
    """
    for rel_root, dirs, files in os.walk(path):
        for filename in files:
            filename = os.path.join(rel_root, filename)

            if not valid_filename(filename, filefilter):
                continue

            yield filename

# ./translations/lib/types/pot.py
def guess_language(filename):
    """Guess a language from the filename."""
    if 'LC_MESSAGES' in filename:
        fp = filename.split('LC_MESSAGES')
        return os.path.basename(fp[0][:-1:])
    else:
        return os.path.basename(filename[:-3:])

