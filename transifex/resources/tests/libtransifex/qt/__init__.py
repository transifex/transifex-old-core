import os
import unittest
from txcommon.tests.base import BaseTestCase
from languages.models import Language
from resources.models import *
from resources.libtransifex.qt import LinguistHandler

class QTFile(BaseTestCase):
    """Suite of tests for the qt lib."""
    def test_qt_parser(self):
        """TS file tests."""
        # Parsing POT file
        handler = LinguistHandler('%s/en.ts' %
            os.path.split(__file__)[0])

        handler.parse_file(True)
        self.stringset = handler.stringset
        entities = 0

        for s in self.stringset.strings:
            # Testing if source entity and translation are the same
            if not s.pluralized:
                self.assertEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '%n FILES PROCESSED.':
                self.assertTrue(s.rule in [1, 5])

            # Counting number of entities
            if s.rule == 5:
                entities += 1

        # Asserting number of entities - QT file has 43 entries +1 plural.
        self.assertEqual(entities, 44)

    def test_qt_parser_fi(self):
        """Tests for fi QT file."""
        handler = LinguistHandler('%s/fi.ts' %
            os.path.split(__file__)[0])

        handler.parse_file()
        self.stringset = handler.stringset

        nplurals = 0
        entities = 0

        for s in self.stringset.strings:

            # Testing if source entity and translation are NOT the same
            # XXX: This is not madatory. For example OK could be OK in finnish
            # as well
            #self.assertNotEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '%n FILES PROCESSED.' and s.pluralized:
                nplurals += 1

            entities += 1

        # Asserting nplurals based on the number of plurals of the 
        # '%n FILES PROCESSED.' entity - fi has nplurals=2
        self.assertEqual(nplurals, 2)

        # Asserting number of entities - QT file has 43 entries.
        self.assertEqual(entities, 44)

    def test_qt_save2db(self):
        """Test creating source strings from a QT file works"""
        handler = LinguistHandler('%s/en.ts' %
            os.path.split(__file__)[0])

        handler.parse_file(is_source=True)

        l = Language.objects.get(code='en')

        r = Resource.objects.create(
            slug = 'foo',
            name = 'foo',
            source_language = l)

        handler.bind_resource(r)

        handler.save2db(is_source=True)

        # Check that all 43 entities are created in the db
        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 43)

        # Check that all source translations are there
        self.assertEqual(len( Translation.objects.filter(resource=r,
            language=l)), 44)

        # Import and save the finish translation
        handler.bind_file('%s/fi.ts' % os.path.split(__file__)[0])
        l = Language.objects.by_code_or_alias('fi')
        handler.set_language(l)
        handler.parse_file()

        handler.save2db()

        # Check if all Source strings are untouched
        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 43)

        # Check that all translations are there
        self.assertEqual( len(Translation.objects.filter(resource=r,
            language=l)), 44)

        r.delete()
