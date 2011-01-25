# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from locks.models import Lock
from transifex.resources.models import Resource
from transifex.teams.models import Team
from transifex.languages.models import Language
from transifex.txcommon.tests.base import BaseTestCase
from transifex.txcommon.log import logger
from notification.models import Notice

# These Languages and POFiles should exist:
TEAM_LANG_CODES = ['en_US', 'pt_BR', 'el']


class TestLocking(BaseTestCase):
    def setUp(self):
        self.assertFalse('external.csrf.middleware.CsrfMiddleware' in
            settings.MIDDLEWARE_CLASSES, msg = 'Locking test doesn\'t '
            'work with CSRF Middleware enabled')
        super(TestLocking, self).setUp()
        
        self.assertNoticeTypeExistence("project_resource_language_lock_expiring")
        
        # Set settings for testcase
        settings.LOCKS_PER_USER = 3
        settings.LOCKS_LIFETIME = 10
        settings.LOCKS_EXPIRE_NOTIF = 10

        # Generate URLs
        url_args = [self.resource.project.slug,
            self.resource.slug, self.language.code]
        self.url_lock = reverse('resource_language_lock', args=url_args)
        self.url_unlock = reverse('resource_language_unlock', args=url_args)
        self.url_extend = reverse('resource_language_extend', args=url_args)
        self.url_resource = reverse('resource_detail', args=url_args[:2])
        self.url_start_lotte = reverse('translate_resource', args=url_args)

        # Sanity checks
        self.assertEqual( Lock.objects.all().count(), 0)
        self.assertEqual( Lock.objects.valid().count(), 0)

    def test_lotte(self):
        # Try opening Lotte and check whether resource was locked
        resp = self.client['team_member'].post(self.url_start_lotte, follow = True)
        self.assertEqual( resp.status_code, 200 )
        self.assertEqual( Lock.objects.valid().count(), 1)

    def test_resource_popup_another_user(self):
        """Test how another user sees the resource popup."""
        resp = self.client['maintainer'].post(self.url_lock)
        resp = self.client['team_member'].post(reverse('resource_actions',
            args=[self.project.slug, self.resource.slug, self.language.code]))
        self.assertContains(resp, "User 'maintainer' locked this translation")
        self.assertContains(resp, "Resource cannot be locked")
        self.assertContains(resp, "currently locked by 'maintainer'")
        self.assertNotContains(resp, "unlock")

    def test_unlock_another_user(self):
        resp = self.client['maintainer'].post(self.url_lock)
        for user in ['team_member', 'registered', 'anonymous']:
            resp = self.client[user].post(self.url_unlock, follow=True)
            self.assertContains(
                resp, "You don't have permission", status_code=403,
                msg_prefix="User class '%s' should not be able to unlock this file" % user)

