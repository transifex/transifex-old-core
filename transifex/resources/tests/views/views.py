# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core import serializers
from django.test.client import Client
from languages.models import Language
from resources.models import Resource, Translation
from resources.tests.views.base import ViewsBaseTest

try:
    import json
except ImportError:
    import simplejson as json

class CoreViewsTest(ViewsBaseTest):
    """Test basic view function"""

    def seUp(self):
        super(CoreViewsTest, self).setUp()

    def test_translate(self):
        """
        Test main view for lotte.
        """
        # Check page status
        resp = self.client['maintainer'].get(reverse(
            'translate', args=[self.project.slug,
            self.resource.slug,self.language.code]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'resources/translate.html')

    def test_stringset_handling(self):
        """
        Test AJAX stringset handler.
        """
        #FIXME: Find a way to emulate dataTables in order to test this view
        pass

    def test_resource_details(self):
        """
        Test resource details of a resource.
        """

        # Check details page
        resp = self.client['maintainer'].get(reverse('resource_detail',
            args=[self.project.slug, self.resource.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'resources/resource.html')

        # response.context[-1] holds our extra_context. maybe we should check
        # some of these to make sure they're there?

    def test_resource_delete(self):
        """
        Test resource delete view.
        """

        slug=self.resource.slug
        # Check if resource gets deleted succesfully
        resp = self.client['maintainer'].post(reverse('resource_delete',
            args=[self.project.slug, self.resource.slug]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Resource.objects.filter(slug=slug,
            project__slug=self.project.slug).count(), 0)

    def test_resource_actions(self):
        """
        Test AJAX resource actions.
        """
        resp = self.client['maintainer'].post(reverse('resource_actions',
            args=[self.project.slug, self.resource.slug, self.language.code]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'resources/resource_actions.html')

    def test_project_resources(self):
        """
        Test view that fetches project resources
        """

        resp = self.client['maintainer'].get(reverse('project_resources',
            args=[self.project.slug, 0]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'resources/resource_list_more.html')
        for r in Resource.objects.filter(project=self.project)[0:4]:
            self.assertTrue(r.slug in resp.content)

    def test_clone_language(self):
        #TODO: complete test case when clone is implemented
        pass

    def test_push_translation(self):
        """
        Test translation push view.
        """
        # Create primary language translation. This is needed to push
        # additional translations
        source_trans = Translation(resource=self.resource,
            source_entity=self.source_entity,
            language = self.language,
            string="foobar")
        source_trans.save()

        trans_lang = 'el'
        trans = "foo"
        new_trans = "foo2"
        # Create new translation 
        # FIXME: Test plurals
        resp = self.client['maintainer'].post(reverse('push_translation',
            args=[self.project.slug, trans_lang]),
            json.dumps({'strings':[{'id':self.source_entity.id,'translations':{'other':trans}}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Translation.objects.filter(resource=self.resource,
            language__code = trans_lang, string=trans).count(), 1)

        # Update existing translation
        resp = self.client['maintainer'].post(reverse('push_translation',
            args=[self.project.slug, trans_lang]),
            json.dumps({'strings':[{'id': self.source_entity.id,
                'translations':{'other':new_trans}}]}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Translation.objects.filter(resource=self.resource,
            language__code = trans_lang, string=new_trans).count(), 1)

        source_trans.delete()

    def test_get_details(self):
        """
        Tranlsation details view
        """
        resp = self.client['maintainer'].post(reverse('entity_details_snippet',
            args=[self.source_entity.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'resources/lotte_details.html')
        self.assertTrue(self.source_entity.occurrences in resp.content)
        self.assertTrue(self.source_entity.string in resp.content)

    def test_delete_resource_translations(self):
        """
        Test resource translation deletion
        """
        trans = "foo"
        # Create new translation
        resp = self.client['maintainer'].post(reverse('push_translation',
            args=[self.project.slug, self.language.code]),
            json.dumps({'strings':[{'id':self.source_entity.id,
                'translations': { 'other': trans}}]}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Translation.objects.filter(resource=self.resource,
            language = self.language, string =trans).count(), 0)

        self.assertTrue(Translation.objects.filter(resource=self.resource,
            language=self.language) >1)

        # Delete Translations
        resp = self.client['maintainer'].post(reverse(
            'resource_translations_delete',
            args=[self.project.slug, self.resource.slug,self.language.code]),
            follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Translation.objects.filter(resource=self.resource,
            language = self.language).count(), 0)
