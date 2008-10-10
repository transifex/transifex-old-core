from django.conf import settings

# Methods used for the backend support. Common backend methods go in
# types/.


def get_trans_manager(file_set, source_lang, type, path=''):
    """
    Initializes an appropriate TransManager object, depending
    on the Translation type of the component and return it.
    
    The initialization will raise an exception if the Translation type
    is not specified in the model.
    """   
    tm = get_tm_object(type)
    return tm(file_set, path, source_lang)

def get_tm_class(trans_type):
    """
    Return the appropriate TransManager class.
    
    Keyword arguments:
    trans_type -- The type of the TransManager, used to decide the class
    to be returned.
    
    >>> print get_tm_class('POT')
    translations.lib.types.pot.POTManager

    """
    assert trans_type in settings.TRANS_CHOICES.keys(), (
        "Translation type '%s' is not registered as a supported one." % trans_type)
      
    return ('%(module)s.%(class)s' % {
        'module': settings.TRANS_CLASS_BASE,
        'class': settings.TRANS_CLASS_NAMES[trans_type]})

def get_tm_object(trans_type):
    """
    Return the appropriate TransManager object.
    
    This is a wrapper around get_tm_class which returns
    a browser object, ready to be initialized.

    >>> tm = get_tm_object('POT')
    
    """
    
    from translations.lib.common import import_to_python
    return import_to_python(get_tm_class(trans_type))



