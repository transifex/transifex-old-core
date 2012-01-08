# -*- coding: utf-8 -*-
import os
from django.core import management
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models.loading import get_model
from django.db import (connections, DEFAULT_DB_ALIAS,
        transaction, IntegrityError)
from django.test import TestCase
from django.test.testcases import (connections_support_transactions,
        disable_transaction_methods, restore_transaction_methods)
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission as DjPermission
from django.contrib.contenttypes.models import ContentType
from django_addons.autodiscover import autodiscover_notifications
from transifex.txcommon.notifications import NOTICE_TYPES
from transifex.txcommon.tests.base import TestCaseMixin


# Load models
Language = get_model('languages', 'Language')
AuPermission = get_model('authority', 'Permission')
Project = get_model('projects', 'Project')
Resource = get_model('resources', 'Resource')
Release = get_model('releases', 'Release')
Team = get_model('teams', 'Team')
SourceEntity = get_model('resources', 'SourceEntity')

# Please refer to the README file in the tests directory for more info about
# the various user roles.
USER_ROLES = [
    'anonymous',
    'registered',
    'maintainer',
    'writer',
    'team_coordinator',
    'team_member']
PASSWORD = '123412341234'


def deactivate_caching_middleware():
    list_middle_c = list(settings.MIDDLEWARE_CLASSES)
    try:
        list_middle_c.remove('django.middleware.cache.FetchFromCacheMiddleware')
    except ValueError:
        pass
    try:
        list_middle_c.remove('django.middleware.cache.UpdateCacheMiddleware')
    except ValueError:
        pass


def deactivate_csrf_middleware():
    list_middle_c = list(settings.MIDDLEWARE_CLASSES)
    try:
        list_middle_c.remove('external.csrf.middleware.CsrfMiddleware')
    except ValueError:
        pass
    settings.MIDDLEWARE_CLASSES = list_middle_c


class Users(TestCaseMixin):
    """A class to create users in setUp().

    Use this as a mixin.
    """

    @classmethod
    def setUpClass(cls):
        registered = Group.objects.get(name="registered")
        registered.permissions.add(
            DjPermission.objects.get_or_create(
                codename='add_project', name='Can add project',
                content_type=ContentType.objects.get_for_model(Project))[0])

        cls.user = {}
        cls.client = {}

        # Create users, respective clients and login users
        for nick in USER_ROLES:
            cls.client[nick] = Client()
            if nick != 'anonymous':
                # Create respective users
                try:
                    cls.user[nick] = User.objects.create_user(
                        nick, '%s@localhost' % nick, PASSWORD)
                except IntegrityError, e:
                    cls.user[nick] = User.objects.get(username=nick)
                cls.user[nick].groups.add(registered)
                # Login non-anonymous personas
                cls.client[nick].login(username=nick, password=PASSWORD)
                #cls.assertTrue(cls.user[nick].is_authenticated())
        cls.client_dict = cls.client
        super(Users, cls).setUpClass()


class NoticeTypes(TestCaseMixin):
    """A class to create default notice types.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        from django.core import management
        management.call_command('txcreatenoticetypes', verbosity=0)
        super(NoticeTypes, cls).setUpClass()


class TransactionNoticeTypes(TestCaseMixin):
    """A class to create default notice types.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        from django.core import management
        management.call_command('txcreatenoticetypes', verbosity=0)
        super(TransactionNoticeTypes, cls).setUpClass()


class Languages(TestCaseMixin):
    """A class to create default languages.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        from django.core import management
        management.call_command('txlanguages', verbosity=0)
        cls.language = Language.objects.get(code='pt_BR')
        cls.language_en = Language.objects.get(code='en_US')
        cls.language_ar = Language.objects.get(code='ar')
        #self.language_hi_IN = Language.objects.get(code='hi_IN')
        super(Languages, cls).setUpClass()


class TransactionLanguages(TestCaseMixin):
    """A class to create default languages.

    Use this as a mixin in transaction-based tests.
    """

    @classmethod
    def setUpClass(cls):
        from django.core import management
        management.call_command('txlanguages', verbosity=0)
        cls.language = Language.objects.get(code='pt_BR')
        cls.language_en = Language.objects.get(code='en_US')
        cls.language_ar = Language.objects.get(code='ar')
        super(TransactionLanguages, cls).setUpClass()


class Projects(Users):
    """A class to create sample projects.

    Use this as a mixin in tests.
    """


    @classmethod
    def setUpClass(cls):
        super(Projects, cls).setUpClass()
        cls.project = Project.objects.get(slug='project1')
        cls.project.maintainers.add(cls.user['maintainer'])
        cls.project.owner = cls.user['maintainer']
        cls.project.save()

        cls.project_private = Project.objects.get(slug='project2')
        cls.project_private.maintainers.add(cls.user['maintainer'])
        cls.project_private.owner = cls.user['maintainer']
        cls.project_private.save()


class Resources(Projects):
    """A class to create sample resources.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        # Create a resource
        super(Resources, cls).setUpClass()
        cls.resource = Resource.objects.get_or_create(
            slug="resource1", name="Resource1", project=cls.project,
            i18n_type='PO'
        )[0]
        cls.resource_private = Resource.objects.get_or_create(
            slug="resource1", name="Resource1", project=cls.project_private,
            i18n_type='PO'
        )[0]


class SourceEntities(Resources):
    """A class to create some sample source entities.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        super(SourceEntities, cls).setUpClass()
        cls.source_entity = SourceEntity.objects.get_or_create(
            string='String1', context='Context1', occurrences='Occurrences1',
            resource=cls.resource
        )[0]
        cls.source_entity_private = SourceEntity.objects.get_or_create(
            string='String1', context='Context1', occurrences='Occurrences1',
            resource=cls.resource_private
        )[0]
        cls.source_entity_plural = SourceEntity.objects.get_or_create(
            string='pluralized_String1', context='Context1',
            occurrences='Occurrences1_plural', resource= cls.resource,
            pluralized=True
        )[0]
        cls.source_entity_plural_private = SourceEntity.objects.get_or_create(
            string='pluralized_String1', context='Context1',
            occurrences='Occurrences1_plural', resource= cls.resource_private,
            pluralized=True
        )[0]


class Translations(SourceEntities):
    """A class to create some sample translations.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        # Create one translation
        super(Translations, cls).setUpClass()
        cls.translation_en = cls.source_entity.translations.get_or_create(
            string='Buy me some BEER :)',
            rule=5,
            source_entity=cls.source_entity,
            language=cls.language_en,
            user=cls.user['registered'],
            resource=cls.resource
        )[0]
        cls.translation_ar = cls.source_entity.translations.get_or_create(
            string=u'This is supposed to be arabic text! αβγ',
            rule=5,
            source_entity=cls.source_entity,
            language=cls.language_ar,
            user=cls.user['registered'],
            resource=cls.resource
        )[0]


class SampleData(Languages, Translations, NoticeTypes):
    """A class that has all sample data defined."""


class BaseTestCase(Languages, NoticeTypes, Translations, TestCase):
    """Provide a solid test case for all tests to inherit from."""

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)

        # Useful for writing tests: Enter ipython anywhere w/ ``self.ipython()``
        try:
            from IPython.frontend.terminal.embed import InteractiveShellEmbed as shell
            self.ipython = shell()
        except ImportError:
            pass

        #FIXME: This should not happen, since it diverges away the test suite
        # from the actual deployment.
        # Remove the caching middlewares because they interfere with the
        # anonymous client.
        deactivate_caching_middleware()
        deactivate_csrf_middleware()
        # Disable actionlog, which in turn disables noticetype requirement.
        settings.ACTIONLOG_ENABLED = False

    @classmethod
    def setUpClass(cls):
        """Set up a sample set of class wide base objects for inherited tests.
        NOTE: Use this Test Suite with
          TEST_RUNNER = 'txtestrunner.runner.TxTestSuiteRunner'
        in settings.
        If you are inheriting the class and overriding setUpClass, don't forget to
        call super::

          from transifex.txcommon.tests import (base2, utils)
          class TestClassName(base2.BaseTestCase):
              @classmethod
              def setUpClass(self):
                  super(TestClassName, self).setUpClass()

        """
        super(BaseTestCase, cls).setUpClass()

        # Add django-authority permission for writer
        cls.permission = AuPermission.objects.create(
            codename='project_perm.submit_translations',
            approved=True, user=cls.user['writer'],
            content_object=cls.project, creator=cls.user['maintainer'])

        # Create teams
        cls.team = Team.objects.get_or_create(language=cls.language,
            project=cls.project, creator=cls.user['maintainer'])[0]
        cls.team_private = Team.objects.get_or_create(language=cls.language,
            project=cls.project_private, creator=cls.user['maintainer'])[0]
        cls.team.coordinators.add(cls.user['team_coordinator'])
        cls.team.members.add(cls.user['team_member'])
        cls.team_private.coordinators.add(cls.user['team_coordinator'])
        cls.team_private.members.add(cls.user['team_member'])

        # Create a release
        cls.release = Release.objects.get_or_create(slug="releaseslug1",
            name="Release1", project=cls.project)[0]
        cls.release.resources.add(cls.resource)
        cls.release_private = Release.objects.get_or_create(slug="releaseslug2",
            name="Release2", project=cls.project_private)[0]
        cls.release_private.resources.add(cls.resource_private)


        # Create common URLs
        # Easier to call common URLs in your view/template unit tests.
        cls.urls = {
            'project': reverse('project_detail', args=[cls.project.slug]),
            'project_edit': reverse('project_edit', args=[cls.project.slug]),
            'resource': reverse('resource_detail', args=[cls.resource.project.slug, cls.resource.slug]),
            'resource_actions': reverse('resource_actions', args=[cls.resource.project.slug, cls.resource.slug, cls.language.code]),
            'resource_edit': reverse('resource_edit', args=[cls.resource.project.slug, cls.resource.slug]),
            'translate': reverse('translate_resource', args=[cls.resource.project.slug, cls.resource.slug, cls.language.code]),
            'release': reverse('release_detail', args=[cls.release.project.slug, cls.release.slug]),
            'release_create': reverse('release_create', args=[cls.project.slug]),
            'team': reverse('team_detail', args=[cls.resource.project.slug,
                                                 cls.language.code]),

            'project_private': reverse('project_detail', args=[cls.project_private.slug]),
            'resource_private': reverse('resource_detail', args=[cls.resource_private.project.slug, cls.resource_private.slug]),
            'translate_private': reverse('translate_resource', args=[cls.resource_private.project.slug, cls.resource_private.slug, cls.language.code]),
        }


        from django.core import management
        management.call_command('txstatsupdate', verbosity=0)

    def _pre_setup(self):
        if not connections_support_transactions():
            if getattr(self, 'multi_db', False):
                databases = connections
            else:
                databases = [DEFAULT_DB_ALIAS]
            for db in databases:
                call_command('flush', verbosity=0, interactive=False, database=db)

        else:
            if getattr(self, 'multi_db', False):
                databases = connections
            else:
                databases = [DEFAULT_DB_ALIAS]

            for db in databases:
                transaction.enter_transaction_management(using=db)
                transaction.managed(True, using=db)
            disable_transaction_methods()

    def _post_teardown(self):
        if connections_support_transactions():
            # If the test case has a multi_db=True flag, teardown all databases.
            # Otherwise, just teardown default.
            if getattr(self, 'multi_db', False):
                databases = connections
            else:
                databases = [DEFAULT_DB_ALIAS]

            restore_transaction_methods()
            for db in databases:
                transaction.rollback(using=db)
                transaction.leave_transaction_management(using=db)
            for connection in connections.all():
                connection.close()

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.client = self.client_dict


    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def create_more_entities(self, total=1):
        """A method to create more entities for those tests that require them."""
        self.source_entity2 = SourceEntity.objects.create(string='String2',
            context='Context1', occurrences='Occurrences1', resource=self.resource)
        self.translation_en2 = self.source_entity2.translations.create(
            string='Translation String 2',
            rule=5,
            source_entity=self.source_entity,
            language=self.language_en,
            user=self.user['registered'])
        self.resource.update_total_entities()
        self.resource.update_wordcount()

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


class BaseTestCase2Tests(BaseTestCase):
    """Test the base test case itself."""

    def test_basetest_users(self):
        """Test that basic users can function normally."""
        for role in USER_ROLES:
            print role
            # All users should be able to see the homepage
            resp = self.client[role].get('/')
            self.assertEquals(resp.status_code, 200)

