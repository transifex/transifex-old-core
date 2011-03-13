# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from transifex.resources.models import RLStats, Resource
from transifex.storage.models import StorageFile
from transifex.storage.tests.api import BaseStorageTests

class ProjectResourceAPITests(BaseStorageTests):
    """
    Test the status codes.
    """
    def test_resource_creation(self):
        """Test creation of resource through the API."""

        self.create_storage()

        data = '{"uuid": "%s"}' % self.uuid
        resp = self.client['registered'].post(reverse('api_project_files',
            args=[self.project.slug]), data, content_type="application/json")
        self.assertTrue('Forbidden access' in resp.content)
        self.assertEqual(resp.status_code, 403)

        resp = self.client['maintainer'].post(reverse('api_project_files',
            args=[self.project.slug]), data, content_type="application/json")
        self.assertEqual(eval(resp.content)['strings_added'], 3)
        self.assertEqual(resp.status_code, 200)

        # To be used in other tests
        self.resource_slug = eval(resp.content)['redirect'].split(
            '/resource/')[1].replace('/','')

        # Some extra check around denormalization
        rls = RLStats.objects.get(resource__project=self.project,
            resource__slug=self.resource_slug, language=self.language_en)

        self.assertEqual(rls.translated, 3)
        self.assertEqual(rls.total, 3)
        self.assertEqual(rls.translated_perc, 100)

    def test_submission_translation(self):
        """Test submission of translation through the API."""

        self.test_resource_creation()

        # Changing language of the storagefile object
        sf = StorageFile.objects.get(uuid=self.uuid)
        sf.language = self.language
        sf.save()

        data = '{"uuid": "%s"}' % self.uuid
        resp = self.client['maintainer'].put(reverse('api_resource_storage',
            args=[self.project.slug, self.resource_slug, self.language.code]),
            data, content_type="application/json")
        self.assertEqual(eval(resp.content)['strings_added'], 3)

        # Some extra check around denormalization
        rls = RLStats.objects.get(resource__project=self.project,
            resource__slug=self.resource_slug, language=self.language)

        resource = Resource.objects.get(project=self.project,
            slug=self.resource_slug)

        self.assertEqual(rls.translated, 3)
        self.assertEqual(rls.total, 3)
        self.assertEqual(rls.translated_perc, 100)
