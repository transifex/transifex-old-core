# -*- coding: utf-8 -*-
from django.test.client import Client
from languages.models import Language
from resources.models import Resource
from txcommon.tests.base import BaseTestCase


class StatusCodesTest(BaseTestCase):
    """Test that all app URLs return correct status code."""
    # TODO: Fill in the urls

    def setUp(self):
        super(StatusCodesTest, self).setUp()
        self.pages = {
            200: [
                ('/projects/p/%s/resource/%s/' %
                    (self.project.slug, self.resource.slug)),
                ('/projects/p/%s/resource/%s/l/en-US/view/' %
                    (self.project.slug, self.resource.slug)),
                ],
            404: [
                'projects/p/f00/resource/b4r/',
                ]}

    def testStatusCode(self):
        """Test that the response status code is correct"""

        client = Client()
        for expected_code, pages in self.pages.items():
            for page_url in pages:
                page = client.get(page_url)
                self.assertEquals(page.status_code, expected_code,
                    "Status code for page '%s' was %s instead of %s" %
                    (page_url, page.status_code, expected_code))
