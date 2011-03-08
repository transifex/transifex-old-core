# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test.client import Client
from transifex.txcommon.tests.base import BaseTestCase

class ReleasesViewsTests(BaseTestCase):

    # Note: The Resource lookup field is tested in the resources app.

    def test_release_create_good_private_resources(self):
        """Test Release creation with private resources.
        
        User with access to a private resource should be able to add it to a
        release.
        """

        url_release_create = reverse('release_create', args=[self.project.slug])
        resp = self.client['maintainer'].post(url_release_create,
            {'slug': 'nice-release', 'name': 'Nice Release',
            'project': self.project.id, 'resources': '|2|',
            'description': '', 'release_date': '', 'resources_text': '',
            'stringfreeze_date': '', 'homepage': '', 'long_description': '',
             'develfreeze_date': '', }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "projects/release_detail.html")

        # Test that a maintainer can see the private resource.
        resp = self.client['maintainer'].get(reverse('release_detail',
            args=[self.project.slug, 'nice-release']))
        self.assertContains(resp, "Release 'Nice Release'", status_code=200)
        self.assertContains(resp, "1 private resources you have access to.")
        self.assertContains(resp, "Portuguese (Brazilian)")

        # Priv proj member can see the private resource.
        resp = self.client['team_member'].get(reverse('release_detail',
            args=[self.project.slug, 'nice-release']))
        self.assertContains(resp, "Release 'Nice Release'", status_code=200)
        self.assertContains(resp, "1 private resources you have access to.")
        self.assertContains(resp, "Portuguese (Brazilian)")

        # Priv proj non-member cannot see the private resource.
        resp = self.client['registered'].get(reverse('release_detail',
            args=[self.project.slug, 'nice-release']))
        self.assertContains(resp, "Release 'Nice Release'", status_code=200)
        self.assertNotContains(resp, "private resources")
        self.assertNotContains(resp, "Portuguese (Brazilian)")

        # ...even if he is a member of the public project teams.
        resp = self.client['registered'].get(reverse('release_detail',
            args=[self.project.slug, 'nice-release']))
        self.team.members.add(self.user['registered'])
        self.assertTrue(self.user['registered'] in self.team.members.all())
        self.assertContains(resp, "Release 'Nice Release'", status_code=200)
        self.assertNotContains(resp, "private resources")
        self.assertNotContains(resp, "Portuguese (Brazilian)")


    def test_release_create_bad_private_resources(self):
        """Test Release creation with private resource w/o access.
        
        Public project release with a private resource I don't have access to.
        Use the registered user as the giunea pig.
        """
        self.project.maintainers.add(self.user['registered'])
        self.assertFalse(self.user['registered'] in self.project_private.maintainers.all())
        url_release_create = reverse('release_create', args=[self.project.slug])
        r = self.client['registered'].post(url_release_create,
            {'slug': 'nice-release', 'name': 'Nice Release',
            'project': self.project.id, 'resources': '|2|',
            'description': '', 'release_date': '', 'resources_text': '',
            'stringfreeze_date': '', 'homepage': '', 'long_description': '',
             'develfreeze_date': '', }, follow=True)
        # The release shouldn't even be allowed to be created.
        self.assertFalse(self.project.releases.get(slug='nice-release'))
        self.assertTemplateUsed(resp, "projects/release_form.html")
        self.assertContains(resp, "Invalid...")

