# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test.client import Client
from transifex.projects.models import Project
from transifex.txcommon.tests.base import BaseTestCase

class TestTimeline(BaseTestCase):

    def setUp(self):
        super(TestTimeline, self).setUp()

        # Sanity checks
        self.assertTrue( Project.objects.count() >= 1, msg = "Base test case didn't create any projects" )

        # Generate timeline URLs
        self.url_user_timeline = reverse("user_timeline")
        self.url_user_profile = reverse("profile_overview")
        self.url_project_timeline = reverse('project_timeline', args=[self.project.slug])


    def test_anon(self):
        """
        Test anonymous user
        """
        # Check user timeline page as anonymous user
        resp = self.client['anonymous'].get( self.url_user_timeline, follow = True )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("Enter your username and password to sign in." in resp.content)

        # Check project timeline page as anonymous user
        resp = self.client['anonymous'].get( self.url_project_timeline, follow = True )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("Enter your username and password to sign in." in resp.content)

    def test_regular(self):
        """
        Test regular registered user
        """

        # Check user timeline page as regular user
        resp = self.client['registered'].get( self.url_user_timeline )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("Timeline" in resp.content)
        self.assertTrue("Filter results" in resp.content)
        a = ("The query returned " in resp.content)
        b = ("None available" in resp.content)
        self.assertTrue( a or b)

        # Check project timeline page as regular user
        resp = self.client['registered'].get( self.url_project_timeline )
        self.assertEqual(resp.status_code, 200)

        # Check private project timeline page as regular user
        resp = self.client['registered'].get(
            reverse('project_timeline', args=[self.project_private.slug]))
        self.assertEqual(resp.status_code, 403)

        # Anonymous should require a login
        resp = self.client['anonymous'].get( self.url_project_timeline, follow=True)
        self.assertTrue("Enter your username and password to sign in." in resp.content)

        # Check whether link to user timeline is injected to profile page
        resp = self.client['registered'].get( self.url_user_profile )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("My Timeline" in resp.content)

    def test_maint(self):
        """
        Test maintainer
        """

        # Check user timeline page as regular user
        resp = self.client['registered'].get( self.url_user_timeline )
        self.assertEqual(resp.status_code, 200)

        # Check project timeline as maintainer
        resp = self.client['maintainer'].get( self.url_project_timeline )
        self.assertEqual(resp.status_code, 200)

        # Fetch project overview page
        resp = self.client['maintainer'].get(self.urls['project'])
        self.assertEqual(resp.status_code, 200)

        # Check whether link to timeline page is found on the page
        self.assertTrue( self.url_project_timeline in resp.content )

        # Check whether injected History block is included
        self.assertTrue( "History" in resp.content )

