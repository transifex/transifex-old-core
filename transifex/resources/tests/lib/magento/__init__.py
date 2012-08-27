# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
from transifex.resources.models import Translation, SourceEntity
from transifex.resources.formats.magento import MagentoCSVHandler
from transifex.resources.tests.lib.base import FormatsBaseTestCase


class MagentoCSVTestCase(FormatsBaseTestCase):

    def setUp(self):
        super(MagentoCSVTestCase, self).setUp()
        self.resource.i18n_type = 'CSV'
        self.resource.save()
        self.handler = MagentoCSVHandler()
        self.handler.set_language(self.resource.source_language)
        self.handler.bind_resource(self.resource)
        self.source_file = os.path.join(os.path.dirname(__file__),
            'test.csv')
        self.trans_file = os.path.join(os.path.dirname(__file__),
            'translation.csv')
        self.reviewed_trans_file = os.path.join(os.path.dirname(__file__),
            'translation_reviewed.csv')

    def test_parser(self):
        f = open(self.source_file)
        content = f.read()
        f.close()
        self.handler.bind_content(content)
        self.handler.parse_file(True)
        entities = 0
        translations = 0
        for s in self.handler.stringset:
            entities += 1
            if s.translation is not "":
                translations += 1
        self.assertEqual(entities, 5)
        self.assertEqual(translations, 5)

    def _test_save2db(self):
        self.handler.bind_file(self.source_file)
        self.handler.parse_file(True)
        self.handler.save2db(True)
        self.assertEqual(SourceEntity.objects.filter(
            resource=self.resource).count(), 5)
        self.assertEqual(Translation.objects.filter(
            resource=self.resource, language=self.resource.source_language
            ).count(), 5)

        self.handler.set_language(self.language_ar)
        self.handler.bind_file(self.trans_file)
        self.handler.parse_file()
        self.handler.save2db()
        self.assertEqual(SourceEntity.objects.filter(
            resource=self.resource).count(), 5)
        self.assertEqual(Translation.objects.filter(
            resource=self.resource, language=self.language_ar
            ).count(), 3)
        # review a translation
        Translation.objects.filter(resource=self.resource,
            language=self.language_ar, string="string 1").update(
            reviewed=True)

    def _test_compile(self):
        self._check_compilation(self.handler, self.resource,
                self.resource.source_language, self.source_file,
                'DEFAULT'
        )
        self._check_compilation(self.handler, self.resource,
                self.language_ar, self.trans_file,
                'TRANSLATED'
        )
        self._check_compilation(self.handler, self.resource,
                self.language_ar, self.trans_file,
                'DEFAULT'
        )
        self._check_compilation(self.handler, self.resource,
                    self.language_ar, self.reviewed_trans_file,
                    'REVIEWED'
        )

    def test_save_and_compile(self):
        self._test_save2db()
        self._test_compile()
