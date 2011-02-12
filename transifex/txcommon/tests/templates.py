# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from transifex.txcommon.tests.base import BaseTestCase

HOME_URL = reverse('transifex.home')

class TxCommonTemplatesTests(BaseTestCase):

    def test_footer_links_cf(self):
        resp = self.client['anonymous'].get(HOME_URL)
        self.assertTemplateUsed(resp, 'index.html')
        if settings.ENABLE_CONTACT_FORM:
            self.assertContains(resp, "Feedback")
        else:
            self.assertNotContains(resp, "Feedback")

