# -*- coding: utf-8 -*-
from django.conf import settings
from transifex.txcommon import import_to_python

def get_pseudo_class(ptype):
    """Return pseudo type class."""
    return import_to_python(settings.PSEUDO_TYPE_CLASSES[ptype])
  
class PseudoTypeMixin:
    """
    Mixin class to serve as a base for creation of Pseudo class types.
    
    Classes derived from this class can implement custom methods depending
    on the i18n_type. Those custom method names must match the values 
    available for i18n_type (settings.I18N_METHODS.keys()) in lower case 
    and with an underscore in front of it.
    """
    def __init__(self, i18n_type):
        self.method_name = '_%s' % i18n_type.lower()

        # Declare method naming it accordingly to the i18n_type
        if not hasattr(self, self.method_name):
            setattr(self, self.method_name, self._base_compile)

    def _base_compile(self, string):
        raise NotImplementedError("Must be implemented in the child class.")

    # Should not be overridden
    def compile(self, string):
        """Run the correct method depending on the i18n_type."""
        return getattr(self, self.method_name)(string)