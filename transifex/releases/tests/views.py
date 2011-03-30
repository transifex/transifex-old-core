# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test.client import Client
from transifex.txcommon.tests import base, utils

class ReleasesViewsTests(base.BaseTestCase):

    # Note: The Resource lookup field is tested in the resources app.

    def test_release_list(self):
        self.assertTrue(self.project.releases.all())

        # Anonymous and maintainer should see it
        resp = self.client['anonymous'].get(self.urls['project'])
        self.assertContains(resp, self.release.name)
        resp = self.client['maintainer'].get(self.urls['project'])
        self.assertContains(resp, self.release.name)


    def test_release_list_noreleases(self):
        self.project.releases.all().delete()

        # Maintainer should see things
        resp = self.client['maintainer'].get(self.urls['project'])
        self.assertContains(resp, "No releases are registered")

        # Anonymous should not see anything
        resp = self.client['anonymous'].get(self.urls['project'])
        self.assertNotContains(resp, "Project Releases")


    def test_release_details_resources(self):
        """Test whether the right resources show up on details page."""
        resp = self.client['anonymous'].get(self.urls['release'])

        # The list at the top of the page should include this resource.
        self.assertContains(resp, "Test Project: Resource1")

        # One of the languages is totally untranslated.
        self.assertContains(resp, "Untranslated: %s" % self.resource.source_entities.count())


    def test_release_create_good_private_resources(self):
        """Test Release creation with private resources.

        User with access to a private resource should be able to add it to a
        release.
        """

        resp = self.client['maintainer'].post(self.urls['release_create'],
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
        r = self.client['registered'].post(self.urls['release_create'],
            {'slug': 'nice-release', 'name': 'Nice Release',
            'project': self.project.id, 'resources': '|2|',
            'description': '', 'release_date': '', 'resources_text': '',
            'stringfreeze_date': '', 'homepage': '', 'long_description': '',
             'develfreeze_date': '', }, follow=True)
        # The release shouldn't even be allowed to be created.
        self.assertFalse(self.project.releases.get(slug='nice-release'))
        self.assertTemplateUsed(resp, "projects/release_form.html")
        self.assertContains(resp, "Invalid...")

