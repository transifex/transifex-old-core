import unittest
from languages.models import Language

class LanguageModelsTestCase(unittest.TestCase):
    """
    Test Translation Models.
    
    Supplementary tests, in addition to doctests.   
    """

    def test_lang_create(self):
        """
        Test Language creation.
        
        >>> ### Test unique keys
        >>> Language.objects.create(name='Brazilian Portuguese')
        Traceback (most recent call last):
            ...
        IntegrityError: column name is not unique
        >>> Language.objects.create(code='pt_BR')
        Traceback (most recent call last):
            ...
        IntegrityError: column code is not unique
        >>>
        """
