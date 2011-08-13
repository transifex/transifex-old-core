import os
import re
import unittest
from transifex.txcommon.tests.base import BaseTestCase
from transifex.languages.models import Language
from transifex.resources.models import *
from transifex.resources.formats.xliff import XliffHandler

class TestXliffParser(BaseTestCase):
    """Suite of tests for XLIFF file lib."""

    def test_accept(self):
        """Test whether parser accepts XLIFF file format"""
        parser = XliffHandler()
        self.assertTrue(parser.accepts(mime='text/x-xml'))

    def test_xliff_parser(self):
        """XLIFF parsing tests."""
        # Parsing XLIFF content
        files = ['example.xlf']
        for file in files:
            handler = XliffHandler(os.path.join(os.path.dirname(__file__), file))
            handler.set_language(self.resource.source_language)
            handler.parse_file(is_source=True)
            self.stringset = handler.stringset
            entities = 0
            translations = 0
            for s in self.stringset.strings:
                entities += 1
                if s.translation.strip() != '':
                    translations += 1
            self.assertEqual(entities, 7)
            self.assertEqual(translations, 7)

    def test_xliff_save2db(self):
        """Test creating source strings from a XLIFF file"""
        source_file = 'example.xlf'
        trans_file = 'translation_ar.xlf'
        handler = XliffHandler(os.path.join(os.path.dirname(__file__), source_file))
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.bind_resource(self.resource)
        handler.save2db(is_source=True)
        r = self.resource
        l = r.source_language
        # Check that all entities with not null are created in the db
        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 6)

        # Check that all source translations are there
        self.assertEqual(
            len(Translation.objects.filter(source_entity__resource=r, language=l)), 7
        )

        # Import and save the finish translation
        l = self.language_ar
        handler.bind_file(os.path.join(os.path.dirname(__file__), trans_file))
        handler.set_language(l)
        handler.parse_file()

        entities = 0
        translations = 0
        for s in handler.stringset.strings:
            entities += 1
            if s.translation.strip() != '':
                translations += 1
        self.assertEqual(entities, 7)
        self.assertEqual(translations, 7)

        handler.save2db()
        # Check if all Source strings are untouched
        self.assertEqual(SourceEntity.objects.filter(resource=r).count(), 6)
        # Check that all translations are there
        self.assertEqual(len(Translation.objects.filter(source_entity__resource=r,
            language=l)), 7)

        r.delete()

