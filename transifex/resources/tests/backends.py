# -*- coding: utf-8 -*-

import os
import codecs
from django.conf import settings
from django.test import TransactionTestCase
from transifex.projects.models import Project
from transifex.txcommon.tests.base import Languages, Users, NoticeTypes
from transifex.languages.models import Language
from transifex.resources.models import Resource, SourceEntity, Translation
from transifex.resources.backends import *


class TestBackend(Users, Languages, NoticeTypes, TransactionTestCase):

    def setUp(self):
        super(TestBackend, self).setUp()
        file_ = os.path.join(
            settings.TX_ROOT, "resources/tests/lib/pofile/pt_BR.po"
        )
        f = codecs.open(file_, 'r', encoding='UTF-8')
        try:
            self.content = f.read()
        finally:
            f.close()
        self.source_lang = self.language_en
        self.target_lang = self.language
        self.maintainer = self.user['maintainer']
        self.project = Project.objects.create(slug='testp', name='Test Project')
        self.resource = Resource.objects.create(
            slug='test', name='Test', source_language=self.source_lang,
            project=self.project
        )
        self.method = 'PO'


class TestResourceBackend(TestBackend):

    def test_create(self):
        rb = ResourceBackend()
        res = rb.create(
            self.project, slug='test1', name='Test', method=self.method,
            source_language=self.source_lang, content=self.content,
            user=self.maintainer, extra_data={'accept_translations': True}
        )
        r = Resource.objects.get(slug='test')
        self.assertEquals(res[0], 6)
        self.assertEquals(res[1], 0)


class TestFormatsBackend(TestBackend):

    def test_import(self):
        fb = FormatsBackend(self.resource, self.source_lang, self.maintainer)
        res = fb.import_source(self.content, self.method)
        ses = SourceEntity.objects.filter(resource=self.resource)
        trs = Translation.objects.filter(source_entity__in=ses)
        self.assertEquals(res[0], 6)
        self.assertEquals(res[1], 0)
        self.assertEquals(len(ses), 6)
        self.assertEquals(len(trs), 7)


