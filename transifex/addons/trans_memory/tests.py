# -*- coding: utf-8 -*-
from transifex.txcommon.tests.base import BaseTestCase
from transifex.resources.models import SourceEntity

class MemoryViewsTests(BaseTestCase):

    def setUp(self):
        super(MemoryViewsTests, self).setUp()
        self.entity = self.resource.entities[0]
        self.URL_PREFIX = '/search_translations/'

    def testAnonymousPagesStatusCode(self):
        pages = {302: [(self.URL_PREFIX),],}
        self.assert_url_statuses(pages, self.client["anonymous"])

    def test_memory_search(self):
        raise NotImplementedError


    def test_private_project(self):
        """Test access to various methods if the project is private."""
        source_entity = SourceEntity.objects.create(string='String2',
            context='Context2', occurrences='Occurrences1',
            resource=self.resource_private)
        source_entity.translations.create(
            string='This is a test source string',
            rule=5,
            source_entity=source_entity,
            language=self.language_en,
            user=self.user['team_member'])
        source_entity.translations.create(
            string=u'This is supposed to be arabic text! αβγ',
            rule=5,
            source_entity=source_entity,
            language=self.language_ar,
            user=self.user['team_member'])
        DATA = {'tq': 'test string', 'source_lang' : self.language_en.code, 'target_lang' : self.language_ar.code}
        resp = self.client['team_member'].get(self.URL_PREFIX, DATA)
        self.assertContains(resp,'Tough luck! No translations obtained.', status_code=200)

