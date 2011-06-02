# -*- coding: utf-8 -*-
import unittest
from django.conf import settings
from transifex.resources.formats.utils.methods import get_extensions_for_method, \
        get_mimetypes_for_method

class TestFormatsUtilities(unittest.TestCase):
    """
    Test utility functions used in the formats code.
    """

    def test_get_extensions_for_method(self):
        methods = settings.I18N_METHODS
        for m in methods:
            extensions = get_extensions_for_method(m)
            self.assertEquals(len(extensions), len(methods[m]['file-extensions'].split(',')))
            for e in extensions:
                self.assertTrue(' ' not in e)
                self.assertTrue(e[0] == '.')
        self.assertEquals(get_extensions_for_method('u'), [])

    def test_get_mimetypes_for_method(self):
        methods = settings.I18N_METHODS
        for m in methods:
            mimetypes = get_mimetypes_for_method(m)
            self.assertEquals(len(mimetypes), len(methods[m]['mimetype'].split(',')))
            for m in mimetypes:
                self.assertTrue('/' in m)
        self.assertEquals(get_extensions_for_method('m'), [])
