# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from happix.tests.api.base import APIBaseTests

class StringHandlerTests(APIBaseTests):
    """Tests for the StringHandler API."""
    def setUp(self):
        super(StringHandlerTests, self).setUp()
        self.resource_handler_url = reverse('string_resource_push', 
            args=[self.project.slug, self.resource.slug])

    def test_api_get(self):
        """ Test GET method."""
        response = self.client['maintainer'].get(self.resource_handler_url,
            {'languages':'pt_BR,en_US'})

        # Check for a string of the en_US translation
        self.assertContains(response, '"en_US": "{0} results"')

        # Check for a string of the pt_BR translation
        self.assertContains(response, '"pt_BR": "{0} resultados"')

    def test_api_post(self):
        """ Test POST method."""
        response = self.client['maintainer'].post(self.resource_handler_url,
            self.data, 'application/json')

        # FIXME: Authentication through the API is needed here to be able to 
        # create/push strings.
        self.assertEquals(response.content, 'Authorization Required')

    def test_api_put(self):
        """ Test PUT method."""
        response = self.client['maintainer'].put(self.resource_handler_url,
            self.data, 'application/json')

        # FIXME: Authentication through the API is needed here to be able to 
        # create/push strings.
        self.assertEquals(response.content, 'Authorization Required')

    def test_api_delete(self):
        """ Test DELETE method."""
        #response = self.client['maintainer'].delete(self.resource_handler_url,
        #    self.data, 'application/json')
        pass
