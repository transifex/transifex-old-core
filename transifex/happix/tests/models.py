# -*- coding: utf-8 -*-
from django.conf import settings
from django.test import TestCase

from happix.models import *

#from IPython.Shell import IPShellEmbed
#ipython = IPShellEmbed()

SAMPLE_STRING = 'Hello'
SAMPLE_STRINGS = ['%s_%s' % (SAMPLE_STRING, i) for i in range(1, 11)]

class HappixModelTests(TestCase):
    """Test the happix models."""

    def setUp(self):
        pass

    def tearDown(self):
        # Clear up the DB
        pass

    def test_model_tresource(self):
        """
        Test TResource model creation.
        
        """
        pass

    def test_model_source_string(self):
        """
        Test SourceString model.
        
        """
        pass

    def test_model_translation_string(self):
        """
        Test TranslationString model.
        
        """
        pass
