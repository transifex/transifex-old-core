from django.conf import settings
from projects.handlers.common import import_to_python

# Methods used for the backend support. Common backend methods go in
# types/.


def get_trans_handler(i18n_type):
    """
    Return an appropriate TransHandler class.

    TransHandler is chosen depending on the component translation type.
    
    It will raise an exception if the Translation type
    is not specified.
    
    Keyword arguments:
    i18n_type -- The type of the TransHandler, used to decide the class
    to be returned.
    
    >>> print get_trans_handler('POT')
    projects.handlers.trans_handler.TransHandler

    """

    assert i18n_type in settings.TRANS_CHOICES.keys(), (
        "Translation type '%s' is not registered as a supported one." % i18n_type)
      
    class_name = ('%(module)s.%(class)s' % {
                  'module': settings.TRANS_CLASS_BASE,
                  'class': settings.TRANS_CLASS_NAMES[i18n_type]})

    return import_to_python(class_name)


