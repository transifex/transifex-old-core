import os
import unittest
from txcommon.tests.base import BaseTestCase
from languages.models import Language
from resources.models import *
from resources.formats.pofile import POHandler

class POFile(BaseTestCase):
    """Suite of tests for the pofile lib."""
    def test_pot_parser(self):
        """POT file tests."""
        # Parsing POT file
        handler = POHandler('%s/tests.pot' % 
            os.path.split(__file__)[0])

        handler.parse_file()
        self.stringset = handler.stringset
        entities = 0

        # POT has no associated language
        self.assertEqual(self.stringset.target_language, None)

        for s in self.stringset.strings:
            # Testing if source entity and translation are the same
            if not s.pluralized:
                self.assertEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.rule, 5)

            # Counting number of entities
            if s.rule == 5:
                entities += 1

        # Asserting number of entities - POT file has 3 entries.
        self.assertEqual(entities, 3)

    def test_po_parser_pt_BR(self):
        """Tests for pt_BR PO file."""
        handler = POHandler('%s/pt_BR.po' % 
            os.path.split(__file__)[0])

        handler.parse_file()
        self.stringset = handler.stringset

        nplurals = 0

        for s in self.stringset.strings:

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.rule, 5)

            if s.source_entity == '{0} result' and s.pluralized:
                nplurals += 1

        # Asserting nplurals based on the number of plurals of the 
        # '{0 results}' entity - pt_BR has nplurals=2
        self.assertEqual(nplurals, 2)

    def test_po_parser_ar(self):
        """Tests for ar PO file."""
        handler = POHandler('%s/ar.po' % 
            os.path.split(__file__)[0])

        handler.parse_file()
        self.stringset = handler.stringset
        nplurals = 0

        for s in self.stringset.strings:

            # Testing if source entity and translation are NOT the same
            self.assertNotEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.rule, 5)

            if s.source_entity == '{0} result' and s.pluralized:
                nplurals += 1

        # Asserting nplurals based on the number of plurals of the 
        # '{0 results}' entity - ar has nplurals=6.
        self.assertEqual(nplurals, 6)

    def test_po_save2db(self):
        """Test creating source strings from a PO/POT file works"""
        handler = POHandler('%s/tests.pot' % 
            os.path.split(__file__)[0]) 

        handler.parse_file(is_source=True)

        l = Language.objects.get(code='en_US')

        r = Resource.objects.create(
            slug = 'foo',
            name = 'foo',
            source_language = l)

        handler.bind_resource(r)

        handler.save2db(is_source=True)

        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 3)

        self.assertEqual( len(Translation.objects.filter(source_entity__resource=r,
            language=l)), 4)

        handler.bind_file('%s/ar.po' % os.path.split(__file__)[0])
        l = Language.objects.by_code_or_alias('ar')
        handler.set_language(l)
        handler.parse_file()

        handler.save2db()

        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 3)

        self.assertEqual( len(Translation.objects.filter(source_entity__resource=r,
            language=l)), 8)

        r.delete()
