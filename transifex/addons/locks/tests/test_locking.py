# -*- coding: utf-8 -*-
import warnings
from time import sleep
from django.core import management
from django.conf import settings
from django.db.models.loading import get_model, get_app
from django.core.urlresolvers import reverse
from txcommon.tests.base import BaseTestCase
from txcommon.log import logger
from notification.models import Notice

# Load models
POFile = get_model('translations', 'POFile')
Team = get_model('teams', 'Team')
Language = get_model('languages', 'Language')
POFileLock = get_model('locks', 'POFileLock')
POFileLockError = get_app('locks').POFileLockError

# These Languages and POFiles should exist:
TEAM_LANG_CODES = ['en', 'es', 'fr']

# To invoke IPython shell during runtime you can use following piece of code:
# from IPython.Shell import IPShellEmbed
# IPShellEmbed()()

class TestLocking(BaseTestCase):
    def setUp(self):
        self.assertFalse('external.csrf.middleware.CsrfMiddleware' in
            settings.MIDDLEWARE_CLASSES, msg = 'Locking test doesn\'t '
            'work with CSRF Middleware enabled')
        super(TestLocking, self).setUp(create_teams=False)
        self.assertNoticeTypeExistence("project_component_file_lock_expiring")
        
        # Set settings for testcase
        settings.LOCKS_PER_USER = 3
        settings.LOCKS_LIFETIME = 10
        settings.LOCKS_EXPIRE_NOTIF = 10

        # Create teams
        for code in TEAM_LANG_CODES:
            logger.debug("Trying to create team for: %s" % code)
            team = Team()
            team.creator = self.user['maintainer']
            team.language = Language.objects.get(code=code)
            team.project = self.project
            team.save()
            team.members.add(self.user['team_member'])
            team.save()

        # Select first POFile
        self.pofile = self.pofiles.get(language_code = TEAM_LANG_CODES[0])

        # Generate URLs
        url_args = [self.pofile.object.project.slug,
            self.pofile.object.slug, self.pofile.filename]
        self.url_lock = reverse('component_file_lock', args=url_args)
        self.url_unlock = reverse('component_file_unlock', args=url_args)
        self.url_component = reverse('component_detail', args=url_args[:2])
        self.url_submit = reverse('component_submit_file', args=url_args)
        self.url_start_lotte = reverse('component_edit_file', args=url_args)

        # Sanity checks
        self.assertEqual( POFileLock.objects.all().count(), 0)
        self.assertEqual( POFileLock.objects.valid().count(), 0)

    def test_lotte(self):
        # Try opening Lotte and check whether file was locked
        resp = self.client['team_member'].post(self.url_start_lotte, follow = True)
        self.assertEqual( resp.status_code, 200 )
        self.assertEqual( POFileLock.objects.valid().count(), 1)
        POFileLock.objects.all().delete()

        # TODO: Check file unlocking, couldn't find proper way to do it ATM

    def test_submission(self):
        def get_file_handle(pof):
            return open(self.component.trans.tm.get_file_path(pof.filename))

        # Enable submission        
        self.component.allows_submission = True
        self.component.save()

        # Try to submit file as translator: should succeed
        resp = self.client['team_member'].post(self.url_submit, {'submitted_file':
            get_file_handle(self.pofile),'message':'Test'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("File submitted successfully" in resp.content)

        # Try to submit file as maintainer: should succeed
        resp = self.client['maintainer'].post(self.url_submit, {'submitted_file':
            get_file_handle(self.pofile),'message':'Test'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("File submitted successfully" in resp.content)

        # Lock the file
        lock = POFileLock.objects.create_update(self.pofile, self.user['team_member'])
        
        # Get the expiration time of current lock
        expires = self.pofile.locks.get().expires
        sleep(2)

        # Try to submit file as translator: should succeed
        resp = self.client['team_member'].post(self.url_submit, {'submitted_file':
            get_file_handle(self.pofile),'message':'Test'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("File submitted successfully" in resp.content)

        # Make sure expiration time didn't change
        self.assertEqual(self.pofile.locks.get().expires, expires)
        sleep(2)

        # Try to submit file AND EXTEND LOCK: should succeed
        resp = self.client['team_member'].post(self.url_submit, {'submitted_file':
            get_file_handle(self.pofile),'message':'Test', 'lock_extend':'1'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("File submitted successfully" in resp.content)
        self.assertTrue(self.pofile.locks.get().expires > expires,
            "Extend lock checkbox doesn't work")

        # Try to submit file as maintainer: should get 403
        resp = self.client['maintainer'].post(self.url_submit, {'submitted_file':
            get_file_handle(self.pofile),'message':'Test'}, follow=True)
        self.assertEqual(resp.status_code, 403)

        # Delete all locks
        POFileLock.objects.all().delete()


    def test_permissions(self):
        # format: locker : (could_lock, {unlocker : could_unlock}),
        LOCK_PERM_MATRIX = {
            'maintainer' : (
                True,
                {
                    'anonymous':False,
                    'team_member':False,
                    'maintainer' : True
                }),
            'team_member' : (
                True,
                {
                    'anonymous':False,
                    'team_member':True,
                    'maintainer' : True
                }),
            'anonymous' : (False, {'anonymous':False} )
        }

        for locker_nick, (could_lock, unlockers) in LOCK_PERM_MATRIX.iteritems():
            for unlocker_nick, could_unlock in unlockers.iteritems():
                resp = self.client[locker_nick].post(self.url_lock, follow = True)
                if could_lock:
                    logger.debug("Trying to lock as: %s (Should succeed) ..." % locker_nick)
                    self.assertEqual( resp.status_code, 200 )
                    url, code = resp.redirect_chain[0]
                    self.assertTrue( self.url_component in url )
                    self.assertEqual( code, 302 )
                    self.assertEqual( POFileLock.objects.valid().count(), 1)
                    lock = POFileLock.objects.valid().get()
                    self.assertEqual( lock.owner, self.user[locker_nick] )

                    resp = self.client[unlocker_nick].post(self.url_unlock, follow = True)
                    if could_unlock:
                        logger.debug("Trying to unlock as: %s (Should succeed) ..." % unlocker_nick)
                        self.assertEqual( POFileLock.objects.valid().count(), 0)
                    else:
                        logger.debug("Trying to unlock as: %s (Should fail)" % unlocker_nick)                        
                        self.assertEqual( POFileLock.objects.valid().count(), 1)
                else:
                    logger.debug("Trying to lock as: %s (Should fail) ..." % locker_nick)
                    self.assertEqual( POFileLock.objects.valid().count(), 0)
                POFileLock.objects.all().delete()

    def test_main(self):
        """
        Test adding locks
        """
        # Check
        teams = []
        for pofile in self.pofiles:

            value = POFileLock.can_lock(pofile, self.user['team_member'])
            if pofile.language and pofile.language.code in TEAM_LANG_CODES:
                teams.append(pofile.language.code)
                self.assertTrue( value )
            else:
                    self.assertFalse( value )
            # Project maintainers should be able to access locks
            self.assertTrue(POFileLock.can_lock(pofile,
                self.user['maintainer']))
            # Registered but otherwise not associated users shouldn't be able to
            #access locks
            self.assertFalse( POFileLock.can_lock(pofile,
                self.user['registered']))
 
        for team in teams:
            self.assertTrue( team in TEAM_LANG_CODES )

        # Sanity check
        self.assertEqual(POFileLock.objects.valid().count(), 0)
        self.assertEqual(POFileLock.objects.all().count(), 0)

        # Try to lock all files
        for pofile in self.pofiles:
            try:
                POFileLock.objects.create_update(pofile,
                    self.user['team_member'])
                logger.debug("Locked: %s" % pofile)
            except POFileLockError:
                self.assertFalse( pofile.language and pofile.language.code in
                    TEAM_LANG_CODES )

        # Check whether lock was created and is valid
        self.assertEqual(POFileLock.objects.all().count(), len(TEAM_LANG_CODES))
        self.assertEqual(POFileLock.objects.valid().count(),
            len(TEAM_LANG_CODES))

        
        for lock in POFileLock.objects.valid():
            # Check that the lock that exists is for the team we created
            self.assertTrue(lock.pofile.language.code in TEAM_LANG_CODES)

            # Check permissions again
            self.assertFalse(lock.can_unlock(self.user['registered']))
            self.assertTrue(lock.can_unlock(self.user['team_member']))
            self.assertTrue(lock.can_unlock(self.user['maintainer']))

        # No need to actually delete locks because can_unlock is the only
        # constraint for delete_by
        
        # Now sleep and check lock validness again
        logger.debug("Sleeping for %i seconds" % settings.LOCKS_LIFETIME)
        sleep( settings.LOCKS_LIFETIME + 1)

        # Check whether locks expired
        self.assertEqual(POFileLock.objects.all().count(), len(TEAM_LANG_CODES))
        self.assertEqual(POFileLock.objects.valid().count(), 0)

        if settings.ENABLE_NOTICES:
            # TODO: Check mail.outbox also?
            logger.debug("Sending cron_hourly signal to send notifications about "
                "lock expiration")
            management.call_command('cron', interval='hourly')
            self.assertEqual( Notice.objects.count(), len(TEAM_LANG_CODES))
        else:
            warnings.warn("Please set ENABLE_NOTICES to True to run all tests.",
                UserWarning)


        logger.debug("Sending cron_daily signal to clean up database")
        management.call_command('cron', interval='daily')
        self.assertEqual(POFileLock.objects.all().count(), 0)

        self.pofiles = POFile.objects.filter(component = self.component)
        pofile = self.pofiles[0]
