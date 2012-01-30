# -*- coding: utf-8 -*-

"""
Tests for the builders module.
"""

from __future__ import absolute_import
from transifex.txcommon.tests.base import BaseTestCase
from transifex.resources.models import Resource, Translation, SourceEntity
from transifex.resources.formats.compilation import *


class TestTranslationsBuilders(BaseTestCase):
    """Test the various translation builders."""

    def test_all_builder(self):
        """Test that the AllTransaltionsBuilder correctly returns
        all translations.
        """
        builder = AllTranslationsBuilder(self.resource, self.language_en)
        translations = builder()
        self.assertEquals(len(translations), 1)
        self.translation_en.delete()
        translations = builder()
        self.assertEquals(translations, {})

    def test_empty_builder(self):
        """Test that the EmptyTranslationsBuilder always returns an empty
        dictionary.
        """
        builder = EmptyTranslationsBuilder(self.resource, self.language_en)
        translations = builder()
        self.assertEquals(translations, {})
        self.translation_en.delete()
        translations = builder()
        self.assertEquals(translations, {})

    def test_source_builder(self):
        """Test that the SourceTranslationsBuilder uses source strings
        instead of empty translations.
        """
        builder = SourceTranslationsBuilder(self.resource, self.language_ar)
        translations = builder()
        self.assertEquals(len(translations), 1)
        self.translation_ar.delete()
        translations = builder()
        self.assertEquals(len(translations), 1)
