from django.core.urlresolvers import reverse
from django.test.client import Client
from django.contrib.auth.models import User

from languages.models import Language
from txcommon.tests import base, utils

class TestTeams(base.BaseTestCase):

    def setUp(self):
        super(TestTeams, self).setUp()

    def test_team_list(self):
        url = reverse('team_list', args=[self.project.slug])
        resp = self.client['registered'].get(url)
        self.assertContains(resp, '(pt_BR)', status_code=200)

    def test_team_details(self):
        url = reverse('team_detail', args=[self.project.slug, self.language.code])
        resp = self.client['registered'].get(url)
        self.assertContains(resp, '(Brazilian)', status_code=200)

    def test_create_team(self):
        """Test a successful team creation."""
        url = reverse('team_create', args=[self.project.slug])
        # Testmaker POST data:
        # r = self.client.post('/projects/p/desktop-effects/teams/add/', {'language': '1', 'creator': '', 'mainlist': '', 'save_team': 'Save team', 'members_text': '', 'next': '', 'project': '20', 'coordinators': '|1|', 'coordinators_text': '', 'members': '|', 'csrfmiddlewaretoken': 'faac51cbc36b415e98599da53e798bd2', })
        DATA = {'language': self.language_ar.id,
                'project': self.project.id,
                'coordinators': '|%s|' % User.objects.all()[0].id,
                'members': '|',}
        resp = self.client['maintainer'].post(url, data=DATA, follow=True)
        self.assertContains(resp, 'Translation Teams - Arabic', status_code=200)
        self.assertNotContains(resp, 'Enter a valid value')

    def team_details_release(self):
        """Test releases appear correctly on team details page."""
        self.assertTrue(self.project.teams.all().count())
        url = reverse('team_detail', args=[self.project.slug, self.language.code])
        resp = self.client['team_member'].get(url)
        self.assertContains(resp, 'releaseslug', status_code=200)
