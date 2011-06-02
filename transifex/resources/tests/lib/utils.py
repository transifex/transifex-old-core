# -*- coding: utf-8 -*-
import unittest
from django.conf import settings
from transifex.resources.formats.utils.methods import get_extensions_for_method

class TestFormatsUtilities(unittest.TestCase):
    """
    Test utility functions used in the formats code.
    """

    def test_get_extensions_for_method(self):
        methods = settings.I18N_METHODS
        for m in methods.iterkeys():
            extensions = get_extensions_for_method(m)
            self.assertEquals(len(extensions), len(methods[m]['file-extensions'].split(',')))
            for e in extensions:
                self.assertTrue(' ' not in e)
                self.assertTrue(e[0] == '.')
        self.assertEquals(get_extensions_for_method('u'), [])
