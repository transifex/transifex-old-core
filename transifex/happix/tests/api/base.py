# -*- coding: utf-8 -*-
import os
from happix.libtransifex.pofile import POHandler
from happix.models import Resource
from languages.models import Language
from txcommon.tests.base import BaseTestCase
from happix.tests.api.utils import ORIGINAL, TRANSLATION

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
        self.data = ORIGINAL
        self.trans = TRANSLATION
        self.pofile_path = '%s/../libtransifex/pofile' % self.current_path

        # Loading POT (en_US) into the resource
        handler = POHandler('%s/tests.pot' % self.pofile_path)
        handler.parse_file(is_source=True)
        handler.bind_resource(self.resource)
        handler.save2db(is_source=True)

        # Loading PO (pt_BR) into the resource
        handler.bind_file('%s/pt_BR.po' % self.pofile_path)
        handler.set_language(self.language)
        handler.parse_file()
        handler.save2db()

    def tearDown(self):
        super(APIBaseTests, self).tearDown()
        self.resource.delete()
        self.language_en.delete()
