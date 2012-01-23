# -*- coding: utf-8 -*-

from django.utils import unittest
from transifex.txcommon.tests.base import BaseTestCase
from transifex.resources.models import Resource, Translation, SourceEntity
from transifex.resources.formats.compilation import *
from .mode import *


class TestTranslationsBuilders(BaseTestCase):
    """Test the various translation builders."""

    def test_all_builder(self):
        """Test that the AllTransaltionsBuilder correctly returns
        all translations.
        """
        builder = AllTranslationsBuilder(self.resource, self.language_en)
        translations = builder([self.source_entity.id])
        self.assertEquals(len(translations), 1)
        self.translation_en.delete()
        translations = builder([self.source_entity.id])
        self.assertEquals(translations, {})

    def test_empty_builder(self):
        """Test that the EmptyTranslationsBuilder always returns an empty
        dictionary.
        """
        builder = EmptyTranslationsBuilder(self.resource, self.language_en)
        translations = builder([self.source_entity.id])
        self.assertEquals(translations, {})
        self.translation_en.delete()
        translations = builder([self.source_entity.id])
        self.assertEquals(translations, {})


class TestDecoratorBuilders(unittest.TestCase):
    """Test the decorator builders."""

    @staticmethod
    def no_escape(s):
        """Don't escape anything."""
        return s

    @staticmethod
    def a_escape(s):
        """Replace 'a's with 'b's."""
        return s.replace('a', 'b')

    @staticmethod
    def b_escape(s):
        """Inverse of ``a_escape``."""
        return s.replace('b', 'a')

    @classmethod
    def setUpClass(cls):
        super(TestDecoratorBuilders, cls).setUpClass()
        cls.escape_functions = [cls.no_escape, cls.a_escape, cls.b_escape, ]

    def test_normal_builder(self):
        """Test that the normal builder only escapes the string."""
        translation = 'cdefg'
        for func in self.escape_functions:
            builder = NormalDecoratorBuilder(escape_func=func)
            self.assertEquals(translation, builder(translation))
        translation = 'abcdef'
        targets = ['abcdef', 'bbcdef', 'aacdef', ]
        for func, target in zip(self.escape_functions, targets):
            builder = NormalDecoratorBuilder(escape_func=func)
            self.assertEquals(target, builder(translation))

    def test_pseudo_builder(self):
        """Test that the pseudo builder is applied after the
        escape function.
        """
        translation = 'cdefg'
        for func in self.escape_functions:
            builder = PseudoDecoratorBuilder(
                escape_func=self.no_escape,
                pseudo_func=func
            )
            self.assertEquals(translation, builder(translation))
        translation = 'abcdef'
        target = 'aacdef'
        builder = PseudoDecoratorBuilder(
            escape_func=self.a_escape,
            pseudo_func=self.b_escape
        )
        self.assertEquals(target, builder(translation))
        target = 'bbcdef'
        builder = PseudoDecoratorBuilder(
            escape_func=self.b_escape,
            pseudo_func=self.a_escape
        )
        self.assertEquals(target, builder(translation))

    def test_empty_builder(self):
        """Test that the empty builder always returns an empty string."""
        translation = 'abcdef'
        for func in self.escape_functions:
            builder = EmptyDecoratorBuilder(escape_func=func)
            self.assertEquals('', builder(translation))
