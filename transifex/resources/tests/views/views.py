# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core import serializers
from django.test.client import Client
from django.utils import simplejson as json
from transifex.languages.models import Language
from transifex.resources.models import Resource, Translation
from transifex.txcommon.tests import base, utils

class CoreViewsTest(base.BaseTestCase):
    """Test basic view function"""

    def test_resource_details(self):
        """
        Test resource details of a resource.
        """

        # Check details page
        resp = self.client['maintainer'].get(self.urls['resource'])
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
        url = self.urls['resource_actions']

        # Test response for maintainer
        resp = self.client['maintainer'].get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Translate now")
        self.assertTemplateUsed(resp, 'resources/resource_actions.html')

        url_lock = reverse('resource_language_lock', args=[self.project.slug, self.resource.slug, self.language.code])

        # Test response for registered user WITHOUT lock
        resp = self.client['registered'].get(url)
        self.assertContains(resp, "This translation isn't locked")
        self.assertContains(resp, "Translate now")

        # Test response for team_member WITHOUT lock
        resp = self.client['team_member'].get(url)
        self.assertContains(resp, "Lock this translation to notify others")
        self.assertContains(resp, "Translate now")

        # Test response for team_member WITH lock
        resp = self.client['team_member'].post(url_lock)
        resp = self.client['team_member'].get(url)
        self.assertContains(resp, "Translate now")

        # Test response for team_coordinator WITH resource locked by someone else
        resp = self.client['team_coordinator'].get(url)
        self.assertContains(resp, "This resource is currently locked by")

        # Test response for registered user  WITH resource locked by someone else
        resp = self.client['registered'].get(url)
        self.assertContains(resp, "you need to be logged in and a member")

    def test_resource_file_upload(self):
        raise NotImplementedError

    def test_resource_file_download(self):
        """Test that downloading a reosurce with a template file works."""
        # We first need a test that creates a resource with a template.
        raise NotImplementedError
        resp = self.client['registered'].get(
            reverse('download_translation',
            args=[self.project.slug, self.resource.slug, self.language.code]), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('project1_resource1.po' in resp['Content-Disposition'])


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



class ResourceAutofetchTests(base.BaseTestCase):

    def setUp(self, *args, **kwargs):
        super(ResourceAutofetchTests, self).setUp(*args, **kwargs)
        self.SFILE = "http://meego.gitorious.org/meego-netbook-ux/abrt-netbook/blobs/raw/master/po/en_GB.po"
        self.url_edit =  reverse('resource_edit', args=[self.project.slug, self.resource.slug])
        
        
    def test_save_form_url(self):
        """Test that saving the form creates the source URL."""
        resp = self.client['maintainer'].post(self.url_edit, {
            'source_file_url': self.SFILE, 'auto_update': 'on',
            'sourcefile': '', 'accept_translations': 'on',
            'slug': self.resource.slug, 'name': self.resource.name, })
        self.assertEquals(self.resource.url_info.source_file_url, self.SFILE)
        resp = self.client['maintainer'].get(self.url_edit)
        self.assertContains(resp, self.SFILE)
        resp = self.client['anonymous'].get(self.urls['resource'])
        self.assertContains(resp, self.SFILE)

       
    def test_save_form_remove_url(self):
        """Test that saving the form without a source file URL removes it."""

        # First create the source file...
        self.test_save_form_url()

        # Then try to remove it.            
        resp = self.client['maintainer'].post(self.url_edit,
            {'source_file_url': '', 'sourcefile': '',
             'accept_translations': 'on', 'slug': self.resource.slug,
             'name': self.resource.name, })
        resp = self.client['maintainer'].get(self.url_edit)
        self.assertNotContains(resp, self.SFILE)
        resp = self.client['anonymous'].get(self.urls['resource'])
        self.assertNotContains(resp, self.SFILE)


    def test_save_form_url_nourl(self):
        """Test that autofetch without url does not work."""
        resp = self.client['maintainer'].post(self.url_edit,
            {'source_file_url': '', 'auto_update': 'on', 'sourcefile': '',
             'accept_translations': 'on', 'slug': self.resource.slug,
             'name': self.resource.name, })
        self.assertContains(resp, "You have checked the auto update checkbox")



class ReleasesViewsTest(base.BaseTestCase):

    def setUp(self, *args, **kwargs):
        super(ReleasesViewsTest, self).setUp(*args, **kwargs)
        self.release = self.project.releases.create(slug='release1', name='Release1')
        self.release.resources.add(self.resource)

    def test_release_detail_page(self):
        resp = self.client['registered'].get(self.urls['release'])
        self.assertContains(resp, "This release has 1 resource", status_code=200)

        # FIXME: Check if the correct language appears in the table.
        self.assertContains(resp, "Portuguese", status_code=200)
        #raise NotImplementedError('Test if the table has the correct languages.')


class ResourcesLookupsTests(base.BaseTestCase):

    def test_private_resources_ajax_lookup(self):
        """Test that a private resource isn't present in lookup.

        This AJAX lookup/dropdown is present in the Release Add/Edit form.
        """

        public_project = "Test Project: Resource1"
        private_project = "Test Private Project: Resource1"

        # Test that a private project is not visible to a random user
        self.assertTrue(self.user['registered'] not in self.project_private.maintainers.all())
        resp = self.client['registered'].get('/ajax/ajax_lookup/resources', {'q': 'r', 'limit': '150', })
        self.assertContains(resp, public_project, status_code=200)
        self.assertNotContains(resp, private_project, status_code=200)

        # Test that a private project is visible to its maintainer
        self.assertTrue(self.user['maintainer'] in self.project_private.maintainers.all())
        resp = self.client['maintainer'].get('/ajax/ajax_lookup/resources', {'q': 'r', 'limit': '150', })
        self.assertContains(resp, public_project, status_code=200)
        self.assertContains(resp, private_project, status_code=200)

        # Test that a private project is visible to a member of its teams
        self.assertTrue(self.user['team_member'] in self.team_private.members.all())
        self.assertFalse(self.user['team_member'] in self.project_private.maintainers.all())
        resp = self.client['team_member'].get('/ajax/ajax_lookup/resources', {'q': 'r', 'limit': '150', })
        self.assertContains(resp, public_project, status_code=200)
        self.assertContains(resp, private_project, status_code=200)

