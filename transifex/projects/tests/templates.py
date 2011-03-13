# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from transifex.txcommon.tests.base import BaseTestCase


class TemplateTests(BaseTestCase):

    def setUp(self):
        super(TemplateTests, self).setUp()
        #URL
        self.project_detail_url = reverse('project_detail',
            args=[self.project.slug])

    def tearDown(self):
        super(TemplateTests, self).tearDown()
