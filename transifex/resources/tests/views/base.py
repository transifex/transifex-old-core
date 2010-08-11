# -*- coding: utf-8 -*-
import os
from txcommon.tests.base import BaseTestCase
from languages.models import Language
from resources.libtransifex.pofile import POHandler
from resources.models import Resource, SourceEntity

class ViewsBaseTest(BaseTestCase):
    """Tests for resources views."""
    def setUp(self):
        self.current_path = os.path.split(__file__)[0]
        super(ViewsBaseTest, self).setUp()
        self.language_en = Language.objects.get(code='en_US')
        self.resource = Resource(slug="foo", name="foo",
            project=self.project, source_language=self.language_en)
        self.resource.save()
        self.source_entity = SourceEntity(string='test', context='',
            position=1, occurrences='here', resource= self.resource)
        self.source_entity.save()

    def tearDown(self):
        super(ViewsBaseTest, self).tearDown()
        self.resource.delete()
        self.source_entity.delete()
        self.language_en.delete()
