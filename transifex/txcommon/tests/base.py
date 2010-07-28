# -*- coding: utf-8 -*-
import os
from django.contrib.auth import models
from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.conf import settings
from django.db import IntegrityError
from django.db.models.loading import get_model
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client
from django_addons.autodiscover import autodiscover_notifications
from txcommon.notifications import NOTICE_TYPES

from vcs.tests import test_git

# Load models
Project = get_model('projects', 'Project')
Component = get_model('projects', 'Component')
Release = get_model('releases', 'Release')
Team = get_model('teams', 'Team')
Language = get_model('languages', 'Language')
Permission = get_model('authority', 'Permission')
POFile = get_model('translations', 'POFile')

USER_ROLES = [
    'anonymous',
    'registered',
    'maintainer',
    'writer',
    'team_coordinator',
    'team_member']

class BaseTestCase(TestCase):
    """
    Creates a sample set of object such as project, component, release, team,
    users, permission, etc. and does a checkout calculating the po files
    statistics.
    """
    # Use the vcs app git test repo
    root_url = '%s/test_repo/git' % os.path.split(test_git.__file__)[0]

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
       
        #we need to remove the caching middlewares because they interfere with
        #the annonymous client.
        list_middl_c = list(settings.MIDDLEWARE_CLASSES)
        try:
            list_middl_c.remove('django.middleware.cache.FetchFromCacheMiddleware')
        except ValueError:
            pass
        try:
            list_middl_c.remove('django.middleware.cache.UpdateCacheMiddleware')
        except ValueError:
            pass
        try:
            list_middl_c.remove('external.csrf.middleware.CsrfMiddleware')
        except ValueError:
            pass
        settings.MIDDLEWARE_CLASSES = list_middl_c

    def setUp(self, skip_stats = False, create_teams=True):
        """
        Set up project, component and vcsunit. Insert POFile objects.
        """

        # Run management commands
        management.call_command('txcreatelanguages')
        autodiscover_notifications()
        management.call_command('txcreatenoticetypes')

        # Add group 'registered'
        registered, created = Group.objects.get_or_create(name = "registered")

        # Set proper permission to the 'registered' group
        registered.permissions.add(
            models.Permission.objects.get_or_create(
                codename='add_project', name='Can add project',
                content_type=ContentType.objects.get_for_model(Project))[0])

        self.user = {}
        self.client = {}
        self.client['anonymous'] = Client()
        resp = self.client['anonymous'].get('/')
        self.assertEquals(resp.status_code, 200)
        prefix = 'test_suite'
        password = '123412341234'
        for nick in USER_ROLES:
            if nick != 'anonymous':
                try:
                    user = User.objects.create_user('%s_%s' % (prefix, nick),
                        '%s_%s@localhost' % (prefix, nick), password)
                except IntegrityError:
                    user = User.objects.get(username='%s_%s' % (prefix, nick))
                user.groups.add(registered)
                self.user[nick] = user

                client = Client()
                self.assertTrue(client.login(
                    username = '%s_%s' % (prefix, nick), password = password))
                self.client[nick] = client

        # Create a project, a component/vcsunit a release, and a pt_BR team
        self.project, created = Project.objects.get_or_create(
            slug="test_project", name="Test Project")
        self.project.maintainers.add(self.user['maintainer'])

        self.component, created = Component.objects.get_or_create(
            slug='test_component', project=self.project, i18n_type='POT',
            file_filter='po/.*')
        self.component.set_unit(self.root_url, 'git', 'master')

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



        if not skip_stats:
            # Do a repo checkout and calculate the po file stats
            self.component.prepare()
            self.component.trans.set_stats()
 
            # Fetch pofiles
            self.pofiles = POFile.objects.filter(component = self.component)
            self.assertNotEqual(self.pofiles, None)
        else:
            self.pofiles = None          

    def tearDown(self):
        self.project.delete()
        for nick, user in self.user.iteritems():
            user.delete()

    def assertNoticeTypeExistence(self, noticetype_label):
        """
        Test if noticetype was added
        """
        found = False
        for n in NOTICE_TYPES:
             if n["label"] == noticetype_label:
                 found = True
        self.assertTrue(found, msg = "Notice type '%s' wasn't "
            "added" % noticetype_label)
