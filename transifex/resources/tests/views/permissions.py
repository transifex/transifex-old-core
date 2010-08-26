# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core import serializers
from django.test.client import Client
from languages.models import Language
from resources.models import Resource
from txcommon.tests.base import BaseTestCase

try:
    import json
except ImportError:
    import simplejson as json

class PermissionsTest(BaseTestCase):
    """Test view permissions"""

    def seUp(self):
        super(ViewsTest, self).setUp()

    def test_anon(self):
        """
        Test anonymous user
        """
        # Test main lotte page
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/login/?next=%s' % page_url)

        trans = "foo"
        # Create new translation
        resp = self.client['anonymous'].post(reverse('push_translation',
            args=[self.project.slug, self.language.code,]),
            json.dumps({'strings':[{'id':self.source_entity.id,'translation':trans}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 302)

        # Delete Translations
        resp = self.client['anonymous'].post(reverse(
            'resource_translations_delete',
            args=[self.project.slug, self.resource.slug,self.language.code]))
        self.assertEqual(resp.status_code, 403)

        # Check if resource gets deleted succesfully
        resp = self.client['anonymous'].get(reverse('resource_delete',
            args=[self.project.slug, self.resource.slug]))
        self.assertEqual(resp.status_code, 403)

    def test_registered(self):
        """
        Test random registered user
        """

        # Test main lotte page
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)

        trans = "foo"
        # Create new translation
        resp = self.client['registered'].post(reverse('push_translation',
            args=[self.project.slug, self.language.code,]),
            json.dumps({'strings':[{'id':self.source_entity.id,'translation':trans}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 403)

        # Delete Translations
        resp = self.client['registered'].post(reverse(
            'resource_translations_delete',
            args=[self.project.slug, self.resource.slug,self.language.code]))
        self.assertEqual(resp.status_code, 403)

        # Check if resource gets deleted succesfully
        resp = self.client['registered'].get(reverse('resource_delete',
            args=[self.project.slug, self.resource.slug]))
        self.assertEqual(resp.status_code, 403)

    def test_team_member(self):
        """
        Test team_member permissions
        """

        # Test main lotte page
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        # Test main lotte page for other team. This should fail
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, 'el'])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)

        trans = "foo"
        # Create new translation
        resp = self.client['team_member'].post(reverse('push_translation',
            args=[self.project.slug, self.language.code,]),
            json.dumps({'strings':[{'id':self.source_entity.id,'translation':trans}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 200)

        # Create new translation in other team. Expect this to fail
        resp = self.client['team_member'].post(reverse('push_translation',
            args=[self.project.slug, 'el']),
            json.dumps({'strings':[{'id':self.source_entity.id,'translation':trans}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 403)

        # Delete Translations
        resp = self.client['team_member'].post(reverse(
            'resource_translations_delete',
            args=[self.project.slug, self.resource.slug,self.language.code]))
        self.assertEqual(resp.status_code, 403)

        # Check if resource gets deleted
        resp = self.client['team_member'].get(reverse('resource_delete',
            args=[self.project.slug, self.resource.slug]))
        self.assertEqual(resp.status_code, 403)


    def test_maintainer(self):
        """
        Test maintainer permissions
        """

        # Test main lotte page
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        trans = "foo"
        # Create new translation
        resp = self.client['maintainer'].post(reverse('push_translation',
            args=[self.project.slug, self.language.code,]),
            json.dumps({'strings':[{'id':self.source_entity.id,'translation':trans}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 200)

        # Delete Translations
        resp = self.client['maintainer'].post(reverse(
            'resource_translations_delete',
            args=[self.project.slug,
            self.resource.slug,self.language.code]),follow=True)
        self.assertEqual(resp.status_code, 200)

        # Check if resource gets deleted succesfully
        resp = self.client['maintainer'].get(reverse('resource_delete',
            args=[self.project.slug, self.resource.slug]))
        self.assertEqual(resp.status_code, 200)
