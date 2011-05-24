# -*- coding: utf-8 -*-

from django.conf import settings
from transifex.txcommon.tests.base import BaseTestCase
from transifex.projects.models import Project
from handlers import *
from models import Gtranslate
from transifex.addons.gtranslate import is_gtranslate_allowed

class TestGtranslate(BaseTestCase):

    def test_initial_set(self):
        settings.DISALLOWED_SLUGS = []
        pr = Project(slug='not')
        pr.name = "Dont'w want"
        pr.save()
        settings.DISALLOWED_SLUGS.append('not')
        o = Project(slug='outsourced')
        o.name = "Dont'w want"
        o.save()
        o.outsource = pr
        o.save()
        g = Gtranslate.objects.get(project=o)
        self.assertTrue(g.use_gtranslate)
        p = Project(slug='ok')
        p.name = "Wants"
        p.save()
        g = Gtranslate.objects.get(project=p)
        self.assertTrue(g.use_gtranslate)

    def test_is_allowed(self):
        settings.DISALLOWED_SLUGS = []
        p = Project(slug='yes')
        p.name = 'Yes'
        p.save()
        self.assertTrue(is_gtranslate_allowed(p))
        settings.DISALLOWED_SLUGS.append('no')
        p = Project(slug='no')
        p.name = 'No'
        p.save()
        self.assertFalse(is_gtranslate_allowed(p))
        pout = Project(slug='out')
        pout.name = 'Out'
        pout.save()
        pout.outsource = p
        self.assertFalse(is_gtranslate_allowed(pout))

    def test_delete(self):
        p = Project(slug="rm")
        p.name = "RM me"
        p.save()
        delete_gtranslate(p)


