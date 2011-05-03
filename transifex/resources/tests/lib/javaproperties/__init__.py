import os
import unittest
from transifex.txcommon.tests.base import BaseTestCase
from transifex.languages.models import Language
from transifex.resources.models import *
from transifex.resources.formats.javaproperties import  JavaPropertiesHandler

from transifex.addons.suggestions.models import Suggestion

class PropertiesFile(BaseTestCase):
    """Suite of tests for the propertiesfile lib."""
    def test_properties_parser(self):
        """PROPERTIES file tests."""
        # Parsing PROPERTIES file
        handler = JavaPropertiesHandler(os.path.join(os.path.split(__file__)[0],
            'complex.properties'))

        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        self.stringset = handler.stringset
        entities = 0
        translations = 0
        for s in self.stringset.strings:
            entities += 1
            if s.translation.strip() != '':
                translations += 1

        # Asserting number of entities - PROPERTIES file has 23 entries.
        self.assertEqual(entities, 22)
        self.assertEqual(translations, 22)
        
    def test_properties_parser_hi(self):
        """Tests for hi_IN PROPERTIES file."""
        handler = JavaPropertiesHandler(os.path.join(os.path.split(__file__)[0],
            'complex_hi_IN.properties'))

        handler.set_language(self.language)
        handler.parse_file()
        self.stringset = handler.stringset

        entities = 0
        translations = 0

        for s in self.stringset.strings:
            entities += 1
            if s.translation.strip() != '':
                translations += 1

        self.assertEqual(entities, 22)
        self.assertEqual(translations, 22)

        
    def test_properties_save2db(self):
        """Test creating source strings from a PROPERTIES file works"""
        handler = JavaPropertiesHandler(os.path.join(os.path.split(__file__)[0],
            'complex.properties'))

        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)

        r = self.resource
        l = self.resource.source_language

        handler.bind_resource(r)

        handler.save2db(is_source=True)

        # Check that all 23 entities are created in the db
        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 22)

        # Check that all source translations are there
        self.assertEqual(len( Translation.objects.filter(source_entity__resource=r,
            language=l)), 22)
        
        # Import and save the finish translation
        handler.bind_file(os.path.join(os.path.split(__file__)[0],'complex_hi_IN.properties'))
        l = Language.objects.get(code='hi_IN')
        handler.set_language(l)
        handler.parse_file()

        handler.save2db()

        # Check if all Source strings are untouched
        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 22)

        # Check that all translations are there
        self.assertEqual( len(Translation.objects.filter(source_entity__resource=r,
            language=l)), 22)
        
        r.delete()
