from codebases.lib import BrowserMixinBase

class TransManagerError(Exception):
    pass

class TransManagerMixin(BrowserMixinBase):
    
    """
    Implement TransManager-type-agnostic browser functionality.
    
    This mixin class provides methods common to all types of TransManager
    
    """

