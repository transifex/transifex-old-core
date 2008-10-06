import os

class TransManagerError(Exception):
    pass

class TransManagerMixin:
    
    """
    Implement TransManager-type-agnostic browser functionality.
    
    This mixin class provides methods common to all types of TransManager
    
    """

