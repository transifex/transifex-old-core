# -*- coding: utf-8 -*-
import os
import unittest
from django.conf import settings
from django.db.models.loading import get_app
from staticfiles.resolvers import resolve, resolve_for_app

class TestStaticfiles(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_staticfiles(self):
        """
        Test wether django-staticfiles is properly configured.
 
        There are various reasons why this could fail:
         * App not loaded (not in get_apps())
         * models.py missing
         * Addon not appended to STATICFILES_PREPEND_LABEL_APPS
         * STATIC_ROOT is not absolute path
         * STATICFILES_MEDIA_DIRNAMES doesn't include 'media'
        """
        suffix = 'css/icons.css'
        ref = os.path.realpath('%s/locks/media/%s' % (settings.ADDONS_ROOT, suffix))
        path = 'locks/%s' % suffix
        self.assertEqual(ref, resolve_for_app(get_app('locks'), path, False))
        self.assertEqual(ref, resolve(path))

