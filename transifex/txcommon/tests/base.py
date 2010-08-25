# -*- coding: utf-8 -*-
import os
from django.core import management
from django.conf import settings
from django.db.models.loading import get_model
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission as AuthPermission
from django.contrib.contenttypes.models import ContentType
from django_addons.autodiscover import autodiscover_notifications
from txcommon.notifications import NOTICE_TYPES

# Load models
Language = get_model('languages', 'Language')
Permission = get_model('authority', 'Permission')
Project = get_model('projects', 'Project')
Component = get_model('projects', 'Component')
Release = get_model('releases', 'Release')
Team = get_model('teams', 'Team')

USER_ROLES = [
    'anonymous',
    'registered',
    'maintainer',
    'writer',
    'team_coordinator',
    'team_member']
PASSWORD = '123412341234'


def deactivate_caching_middleware():
    list_middl_c = list(settings.MIDDLEWARE_CLASSES)
    try:
        list_middl_c.remove('django.middleware.cache.FetchFromCacheMiddleware')
    except ValueError:
        pass
    try:
        list_middl_c.remove('django.middleware.cache.UpdateCacheMiddleware')
    except ValueError:
        pass


def deactivate_csrf_middleware():
    list_middl_c = list(settings.MIDDLEWARE_CLASSES)
    try:
        list_middl_c.remove('external.csrf.middleware.CsrfMiddleware')
    except ValueError:
        pass
    settings.MIDDLEWARE_CLASSES = list_middl_c


class BaseTestCase(TestCase):
    """Provide a solid test case for all tests to inherit from."""

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
       
        # Remove the caching middlewares because they interfere with the
        # annonymous client.
        #FIXME: This should not happen, since it diverges away the test suite
        # from the actual deployment.
        deactivate_caching_middleware()
        deactivate_csrf_middleware()

    def setUp(self, create_teams=True):
        """Set up project, component and vcsunit. Insert POFile objects."""

        # Run basic management commands
        # TODO: Investigate the use of a fixture for increased speed.
        management.call_command('txlanguages')
        autodiscover_notifications()
        management.call_command('txcreatenoticetypes')

        # Add group 'registered' and set proper permissions
        # FIXME: Should go in a fixture.
        registered, created = Group.objects.get_or_create(name="registered")
        registered.permissions.add(
            AuthPermission.objects.get_or_create(
                codename='add_project', name='Can add project',
                content_type=ContentType.objects.get_for_model(Project))[0])

        self.user = {}
        self.client = {}
        self.client['anonymous'] = Client()

        # Create users and respective clients
        for nick in USER_ROLES:
            if nick != 'anonymous':
                self.user[nick] = User.objects.create_user(nick, PASSWORD)
                self.user[nick].groups.add(registered)
                self.client[nick] = Client()

        # Create a project, a component/vcsunit a release, and a pt_BR team
        self.project, created = Project.objects.get_or_create(
            slug="test_project", name="Test Project")
        self.project.maintainers.add(self.user['maintainer'])

        self.component, created = Component.objects.get_or_create(
            slug='test_component', project=self.project, i18n_type='POT',
            file_filter='po/.*')

        from vcs.tests import test_git
        root_url = '%s/test_repo/git' % os.path.split(test_git.__file__)[0]
        self.component.set_unit(root_url, 'git', 'master')

        self.release = Release.objects.get_or_create(slug="r1", name="r1",
            project=self.project)[0]
#       self.release.components.add(self.component)

        self.language = Language.objects.get(code='pt_BR')
        if create_teams:
            self.team = Team.objects.get_or_create(language=self.language,
                project=self.project, creator=self.user['maintainer'])[0]
            self.team.coordinators.add(self.user['team_coordinator'])
            self.team.members.add(self.user['team_member'])

        # Add django-authority permission for writer
        self.permission = Permission(codename='project_perm.submit_file', 
            approved=True, user=self.user['writer'], 
            content_object=self.project, creator=self.user['maintainer'])
        self.permission.save()


    def tearDown(self):
        self.project.delete()
        for nick, user in self.user.iteritems():
            user.delete()

    # Custom assertions
    def assertNoticeTypeExistence(self, noticetype_label):
        """Assert that a specific noticetype was created."""
        found = False
        for n in NOTICE_TYPES:
             if n["label"] == noticetype_label:
                 found = True
        self.assertTrue(found, msg = "Notice type '%s' wasn't "
            "added" % noticetype_label)

    #FIXME: Port all status checks to this method.
    def assert_url_statuses(self, pages_dict, client):
        """Test whether a list of URLs return the correct status codes.
       
        'pages_dict':
          A dictionary of status codes, each one listing a
          set of pages to test whether they return that status code.
        'client': A django.test.client.Client object.
        
        >>> pages = {200: ['/', '/projects/',],
                     404: ['/foobar'],}
        >>> self.assert_url_statuses(pages, self.client["anonymous"])
        
        """        
        
        for expected_code, pages in pages_dict.items():
            for page_url in pages:
                page = client.get(page_url)
                self.assertEquals(page.status_code, expected_code,
                    "Status code for page '%s' was %s instead of %s" %
                    (page_url, page.status_code, expected_code))


class BaseTestCaseTests(BaseTestCase):
    """Test the base test case itself."""

    def test_basetest_users(self):
        """Test that basic users can function or login successfully."""

        client = Client()
        for role in USER_ROLES:
            # All users should be able to see the homepage
            resp = self.client[role].get('/')
            self.assertEquals(resp.status_code, 200)
            login_success = client.login(username=role, password=PASSWORD)
            if role == "anonymous":
                self.assertFalse(login_success,
                    "Anonymous user should not be able to login.")
            else:
                self.assertFalse(login_success,
                    "Logged-in users should be able to login.")

