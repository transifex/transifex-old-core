# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core import serializers
from django.test.client import Client
from django.utils import simplejson as json
from transifex.languages.models import Language
from transifex.resources.models import Resource, Translation
from transifex.txcommon.tests.base import BaseTestCase

class CoreViewsTest(BaseTestCase):
    """Test basic view function"""

    def test_resource_details(self):
        """
        Test resource details of a resource.
        """

        # Check details page
        resp = self.client['maintainer'].get(reverse('resource_detail',
            args=[self.project.slug, self.resource.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'resources/resource_detail.html')
        # Test if RLStats was created automatically
        self.assertTrue(self.team.language.name.encode('utf-8') in resp.content)

        # response.context[-1] holds our extra_context. maybe we should check
        # some of these to make sure they're there?

    def test_resource_delete(self):
        """
        Test resource delete view.
        """

        slug=self.resource.slug
        # Check if resource gets deleted successfully
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
            self.assertTrue(r.name in resp.content)

    def test_clone_language(self):
        #TODO: complete test case when clone is implemented
        pass

    def test_push_translation(self):
        """
        Test translation push view.
        """
        # Create primary language translation. This is needed to push
        # additional translations
        source_trans = Translation(
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
            json.dumps({'strings':[{'id':source_trans.id,'translations':{'other':trans}}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Translation.objects.filter(source_entity__resource=self.resource,
            language__code = trans_lang, string=trans).count(), 1)

        # Update existing translation
        resp = self.client['maintainer'].post(reverse('push_translation',
            args=[self.project.slug, trans_lang]),
            json.dumps({'strings':[{'id': source_trans.id,
                'translations':{'other':new_trans}}]}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        translations = Translation.objects.filter(source_entity__resource=self.resource,
            language__code = trans_lang, string=new_trans)
        self.assertEqual(translations.count(), 1)

        source_trans.delete()
        translations.delete()


    def test_delete_resource_translations(self):
        """
        Test resource translation deletion
        """
        # Create primary language translation. This is needed to push
        # additional translations
        source_trans = Translation(source_entity=self.source_entity,
            language = self.language,
            string="foobar")
        source_trans.save()

        trans_lang = 'el'
        trans = "foo"
        # Create new translation
        resp = self.client['maintainer'].post(reverse('push_translation',
            args=[self.project.slug, trans_lang]),
            json.dumps({'strings':[{'id':source_trans.id,
                'translations': { 'other': trans}}]}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Translation.objects.filter(source_entity__resource=self.resource,
            language__code = trans_lang, string =trans).count(), 1)

        # Delete Translations
        # Delete source language translations
        delete_url = reverse('resource_translations_delete',
            args=[self.project.slug, self.resource.slug,self.language.code])
        resp = self.client['maintainer'].get(delete_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'resources/resource_translations_confirm_delete.html')

        resp = self.client['maintainer'].post(delete_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'resources/resource_detail.html')
        self.assertEqual(Translation.objects.filter(source_entity__resource=self.resource,
            language = self.language).count(), 0)

        # Delete target language translations
        delete_url_el = reverse('resource_translations_delete',
            args=[self.project.slug, self.resource.slug, trans_lang])
        resp = self.client['maintainer'].get(delete_url_el)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'resources/resource_translations_confirm_delete.html')

        resp = self.client['maintainer'].post(delete_url_el, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'resources/resource_detail.html')
        self.assertEqual(Translation.objects.filter(source_entity__resource=self.resource,
            language__code = trans_lang).count(), 0)

class ReleasesViewsTest(BaseTestCase):
    
    def setUp(self, *args, **kwargs):
        super(ReleasesViewsTest, self).setUp(*args, **kwargs)
        self.release = self.project.releases.create(slug='release1', name='Release1')
        self.release.resources.add(self.resource)

    def test_release_detail_page(self):
        url = reverse('release_detail',
            args=[self.project.slug, self.release.slug])
        resp = self.client['registered'].get(url)
        self.assertContains(resp, "This release has 1 resource", status_code=200)

        # FIXME: Check if the correct language appears in the table.
        self.assertContains(resp, "Portuguese", status_code=200)
        #raise NotImplementedError('Test if the table has the correct languages.')
