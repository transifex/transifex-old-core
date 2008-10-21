import unittest
from translations.models import (Language, POFile)

class TranslationModelsTestCase(unittest.TestCase):
    """
    Test Translation Models.
    
    Supplementary tests, in addition to doctests.   
    """ 

    def setUp(self):
        self.pofile = POFile(object=self.language, lang=self.language)
        self.pofile.save()
    
    def tearDown(self):
        self.pofile.delete()
 

    def test_pofile_stats(self):
        """
        Test pofile statistics.
        
        >>> ps = POFile.stats_for_lang(self.language)
        >>> ps[0].language.code
        pt_BR
        """
