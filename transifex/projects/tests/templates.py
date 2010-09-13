# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from txcommon.tests.base import BaseTestCase


class TemplateTests(BaseTestCase):
    
    def setUp(self):
        super(TemplateTests, self).setUp()
        #URL
        self.project_detail_url = reverse('project_detail', 
            args=[self.project.slug]) 

    def tearDown(self):
        super(TemplateTests, self).tearDown()

    def test_project_number_of_languages(self):
        """Test that project details template contains the project translated langs."""
        for user in ['anonymous', 'registered','team_member', 'maintainer']:
            resp = self.client[user].get(self.project_detail_url)
            self.assertContains(resp,
                                '<td class="number_of_languages">%s</td>' %
                                 len(self.project.available_languages))