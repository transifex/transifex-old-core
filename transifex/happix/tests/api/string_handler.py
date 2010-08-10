# -*- coding: utf-8 -*-
import json
from django.core.urlresolvers import reverse
from django.db.models import get_model
from django.test.client import Client
from happix.models import Resource, Translation, SourceEntity
from happix.tests.api.base import APIBaseTests
from happix.tests.api.utils import create_auth_string

class StringHandlerTests(APIBaseTests):
    """Tests for the StringHandler API."""
    def setUp(self):
        super(StringHandlerTests, self).setUp()
        self.resource_handler_url = reverse('string_resource_push',
            args=[self.project.slug, self.data['resource']])

    def test_api_get(self):
        """ Test GET method."""


        # User info for authentication
        prefix = 'test_suite'
        password = '123412341234'
        nick = 'maintainer'
        username = '%s_%s' % (prefix, nick)

        auth_string = create_auth_string(username, password)
        client = Client()

        # Create resource with initial strings to test GET
        resp = client.post(self.resource_handler_url,json.dumps(self.data),
                                content_type='application/json',
                                HTTP_AUTHORIZATION=auth_string)
        self.assertEqual(resp.status_code, 201)

        response = self.client['maintainer'].get(self.resource_handler_url)
        json_data = json.loads(response.content)[0] # get 1st resource
        # Check that we got all translation strings
        self.assertEqual(len(json_data['strings']),
                            Translation.objects.filter(
                            resource__slug = self.data['resource'],
                            language__code = self.data['language']).count())

        self.assertTrue(self.data['language'] in response.content)
        for t in Translation.objects.filter(
                        resource__slug = self.data['resource'],
                        language__code = self.data['language']):
            self.assertTrue(t.string in response.content)
            self.assertTrue(t.source_entity.context in response.content)



    def test_api_post(self):
        """ Test POST method."""

        # User info for authentication
        prefix = 'test_suite'
        password = '123412341234'
        nick = 'maintainer'
        username = '%s_%s' % (prefix, nick)

        response = self.client['maintainer'].post(self.resource_handler_url,
            self.data, 'application/json')

        self.assertEquals(response.content, 'Authorization Required')

        auth_string = create_auth_string(username, password)
        client = Client()

        # Maintainer should be able to create the tresource
        resp = client.post(self.resource_handler_url,json.dumps(self.data),
                                content_type='application/json',
                                HTTP_AUTHORIZATION=auth_string)
        self.assertEqual(resp.status_code, 201)

        # Check if resource was created
        self.assertEqual(Resource.objects.filter(project = self.project,
                            slug = self.data['resource']).count(), 1)

        # Check source entities
        self.assertEqual(SourceEntity.objects.filter(
                            resource__slug = self.data['resource']).count(),
                            len(self.data['strings']))

        # Check that all strings are there
        self.assertEqual(Translation.objects.filter(
                            resource__slug = self.data['resource'],
                            language__code = self.data['language']).count(),
                            len(self.data['strings']))


        # Regular user should not be able to post.
        # TODO: Fix permissions and then uncomment the following

        #nick = 'registered'
        #username = '%s_%s' % (prefix, nick)
        #auth_string = create_auth_string(username, password)
        #resp = self.client['maintainer'].post(self.resource_project_url,json.dumps(self.data),
        #                                    content_type='application/json',
        #                                    HTTP_AUTHORIZATION=auth_string)
        #self.assertEqual(resp.status_code, 403)

        Resource.objects.get(project = self.project,
                            slug = self.data['resource']).delete()

    def test_api_put(self):
        """ Test PUT method."""

        # PUT has an issue fixed in django 1.1.2 (Django 1.1.1 throws error) 
        # http://code.djangoproject.com/ticket/11371

        # User info for authentication
        prefix = 'test_suite'
        password = '123412341234'
        nick = 'maintainer'
        username = '%s_%s' % (prefix, nick)

        response = self.client['maintainer'].post(self.resource_handler_url,
            self.data, 'application/json')
        self.assertEquals(response.content, 'Authorization Required')

        # Create auth headers
        auth_string = create_auth_string(username, password)
        client = Client()

        handler_url = reverse('string_resource_push',
            args=[self.project.slug, self.data['resource']])

        # Create the resource and source entities
        resp = client.post(self.resource_handler_url,json.dumps(self.data),
                                content_type='application/json',
                                HTTP_AUTHORIZATION=auth_string)
        self.assertEqual(resp.status_code, 201)


        # Create the new translation strings
        resp = client.put(self.resource_handler_url,json.dumps(self.trans),
                                content_type='application/json',
                                HTTP_AUTHORIZATION=auth_string)
        self.assertEqual(resp.status_code, 200)

        # Check that all strings are in the db
        self.assertEqual(Translation.objects.filter(
                            resource__slug = self.trans['resource'],
                            language__code = self.trans['language']).count(),
                            len(self.trans['strings']))

        Resource.objects.get(project = self.project,
                            slug = self.data['resource']).delete()

    def test_api_delete(self):
        """ Test DELETE method."""
        #response = self.client['maintainer'].delete(self.resource_handler_url,
        #    self.data, 'application/json')
        pass
