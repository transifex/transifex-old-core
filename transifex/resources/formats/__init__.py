# -*- coding: utf-8 -*-

import magic
from django.conf import settings
from transifex.txcommon import import_to_python

def get_i18n_type_from_file(filename):
    """
    Return an appropriate Handler class for given file.

    The handler is selected based on the file extension (we could also use the
    file's mimetype).
    
    It will raise an exception if there is no i18n method that can handle this
    file.
    
    Keyword arguments:
    filename -- The file name. Duh
    """
    i18n_type = None
    m = magic.Magic(mime=True)
    # guess mimetype and remove charset
    try:
        mime_type = m.from_file(filename)
    except IOError:
        # We don't have the actual file. Depend on the filename only
        mime_type = None

    for type, info in settings.I18N_METHODS.items():
        if filter(filename.endswith, info['file-extensions'].split(', ')) or\
          mime_type in info['mimetype'].split(', '):
            i18n_type = type
            break
    
    assert i18n_type, (
        "No suitable handler could be found for given file (%s)." % filename)

    return i18n_type

def get_i18n_handler_from_type(i18n_type):
    """
    The same as above but takes a i18n_type as input. Useful for getting a
    handler from a resource.
    """

    assert i18n_type in settings.I18N_METHODS.keys(), (
        "I18n '%s' is not registered as a supported one." % i18n_type)
      
    class_name = ('%(module)s.%(class)s' % {
                  'module': settings.I18N_HANDLER_CLASS_BASE,
                  'class': settings.I18N_HANDLER_CLASS_NAMES[i18n_type]})

    return import_to_python(class_name)



