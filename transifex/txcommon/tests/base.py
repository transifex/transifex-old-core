# -*- coding: utf-8 -*-
import os
from django.core import management
from django.conf import settings
from django.db.models.loading import get_model
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission as DjPermission
from django.contrib.contenttypes.models import ContentType
from django_addons.autodiscover import autodiscover_notifications
from txcommon.notifications import NOTICE_TYPES

# Load models
Language = get_model('languages', 'Language')
AuPermission = get_model('authority', 'Permission')
Project = get_model('projects', 'Project')
Resource = get_model('resources', 'Resource')
Release = get_model('releases', 'Release')
Team = get_model('teams', 'Team')
SourceEntity = get_model('resources', 'SourceEntity')

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

    fixtures = ["sample_users", "sample_site", "sample_languages", "sample_data"]
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
       
        #FIXME: This should not happen, since it diverges away the test suite
        # from the actual deployment.
        # Remove the caching middlewares because they interfere with the
        # annonymous client.
        deactivate_caching_middleware()
        deactivate_csrf_middleware()
        # Disable actionlog, wich in turn disables noticetype requirement.
        settings.ACTIONLOG_ENABLED = False

    def setUp(self):
        """Set up a sample set of base objects for inherited tests.
        
        If you are inheriting the class and overriding setUp, don't forget to
        call super().
        """

        registered = Group.objects.get(name="registered")
        registered.permissions.add(
            DjPermission.objects.get_or_create(
                codename='add_project', name='Can add project',
                content_type=ContentType.objects.get_for_model(Project))[0])

        self.user = {}
        self.client = {}

        # Create users, respective clients and login users
        for nick in USER_ROLES:
            self.client[nick] = Client()
            if nick != 'anonymous':
                # Create respective users
                self.user[nick] = User.objects.create_user(
                    nick, '%s@localhost' % nick, PASSWORD)
                self.user[nick].groups.add(registered)
                # Login non-anonymous personas
                self.client[nick].login(username=nick, password=PASSWORD)
                self.assertTrue(self.user[nick].is_authenticated())

        # Create projects
        self.project = Project.objects.create(
            slug="test_project", name="Test Project")
        self.project.maintainers.add(self.user['maintainer'])

        # Add django-authority permission for writer
        self.permission = AuPermission.objects.create(
            codename='project_perm.submit_file', 
            approved=True, user=self.user['writer'], 
            content_object=self.project, creator=self.user['maintainer'])

        # Create languages and teams
        self.language = Language.objects.get(code='pt_BR')
        self.language_en = Language.objects.get(code='en_US')
        self.language_ar = Language.objects.get(code='ar')
        self.team = Team.objects.get_or_create(language=self.language,
            project=self.project, creator=self.user['maintainer'])[0]
        self.team.coordinators.add(self.user['team_coordinator'])
        self.team.members.add(self.user['team_member'])

        # Create a resources
        self.resource = Resource(slug="resource1", name="Resource1",
            project=self.project, source_language=self.language_en)
        self.resource.save()
        self.source_entity = SourceEntity.objects.create(string='String1',
            context='Context1', occurrences='Occurrences1', resource=self.resource)

        # Create pluralized source entity
        self.source_entity_plural = SourceEntity.objects.create(
            string='pluralized_String1', context='Context1',
            occurrences='Occurrences1_plural', resource= self.resource,
            pluralized=True)

        # Create a release
        self.release = Release.objects.create(slug="releaseslug1",
            name="Release1", project=self.project)
        self.release.resources.add(self.resource)


    def tearDown(self):
        self.project.delete()
        self.resource.delete()
        self.team.delete()
        self.source_entity.delete()
        self.source_entity_plural.delete()
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
        """Test that basic users can function normally."""
        for role in USER_ROLES:
            # All users should be able to see the homepage
            resp = self.client[role].get('/')
            self.assertEquals(resp.status_code, 200)

