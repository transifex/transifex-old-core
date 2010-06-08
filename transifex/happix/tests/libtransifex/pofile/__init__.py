import os
import unittest
from happix.libtransifex.pofile import PofileParser

class POFile(unittest.TestCase):
    """Suite of tests for the pofile lib."""
    def test_pot_parser(self):
        """POT file tests."""
        # Parsing POT file
        self.stringset = PofileParser.parse_file('%s/tests.pot' % 
            os.path.split(__file__)[0])

        entities = 0

        # POT has no associated language
        self.assertEqual(self.stringset.target_language, None)

        for s in self.stringset.strings:
            # Testing if source entity and translation are the same
            self.assertEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.number, 1)
                self.assertEqual(s.singular.number, 0)

            # Counting number of entities
            if s.number == 0:
                entities += 1

        # Asserting number of entities - POT file has 3 entries.
        self.assertEqual(entities, 3)

    def test_po_parser_pt_BR(self):
        """Tests for pt_BR PO file."""
        self.stringset = PofileParser.parse_file('%s/pt_BR.po' % 
            os.path.split(__file__)[0])

        ss, nplurals = None, 1

        for s in self.stringset.strings:
            # Testing if source entity and translation are NOT the same
            self.assertNotEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.singular.number, 0)

                ss=s.singular

            # Counting nplurals for '{0} results' entity
            if ss and s.singular == ss:
                self.assertEqual(s.number, nplurals)
                nplurals += 1

        # Asserting nplurals based on the number of plurals of the 
        # '{0 results}' entity - pt_BR has nplurals=2
        self.assertEqual(nplurals, 2)


    def test_po_parser_ar(self):
        """Tests for ar PO file."""
        self.stringset = PofileParser.parse_file('%s/ar.po' % 
            os.path.split(__file__)[0])

        ss, nplurals = None, 1

        for s in self.stringset.strings:
            # Testing if source entity and translation are NOT the same
            self.assertNotEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.singular.number, 0)

                ss=s.singular

            # Counting nplurals for '{0} results' entity
            if ss and s.singular == ss:
                self.assertEqual(s.number, nplurals)
                nplurals += 1

        # Asserting nplurals based on the number of plurals of the 
        # '{0 results}' entity - ar has nplurals=6.
        self.assertEqual(nplurals, 6)
