# -*- coding: utf-8 -*-
import os
from happix.libtransifex.pofile import PofileParser
from happix.models import Resource
from languages.models import Language
from txcommon.tests.base import BaseTestCase

class APIBaseTests(BaseTestCase):
    """Tests for the ResourceHandler API."""
    def setUp(self):
        self.current_path = os.path.split(__file__)[0]
        super(APIBaseTests, self).setUp()
        self.language_en = Language.objects.get(code='en_US')
        self.resource = Resource(slug="json", name="json", 
            project=self.project, source_language=self.language_en)
        self.resource.save()

        # Opening JSON data for pushing through the API
        self.data = open('%s/data.json' % self.current_path).read()

        self.pofile_path = '%s/../libtransifex/pofile' % self.current_path

        # Loading POT (en_US) into the resource
        self.stringset = PofileParser.parse_file('%s/tests.pot' % 
            self.pofile_path)
        self.resource.merge_stringset(self.stringset, self.language_en)

        # Loading PO (pt_BR) into the resource
        self.stringset = PofileParser.parse_file('%s/pt_BR.po' % 
            self.pofile_path)
        self.resource.merge_stringset(self.stringset, self.language)

    def tearDown(self):
        super(APIBaseTests, self).tearDown()
        self.resource.delete()
        self.language_en.delete()
