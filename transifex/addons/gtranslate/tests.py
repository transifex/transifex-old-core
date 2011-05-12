# -*- coding: utf-8 -*-

from django.conf import settings
from transifex.txcommon.tests.base import BaseTestCase
from transifex.projects.models import Project
from handlers import *
from models import Gtranslate

class TestGtranslate(BaseTestCase):

    def test_initial_set(self):
        pr = Project(slug='not')
        pr.name = "Dont'w want"
        pr.save()
        settings.DISALLOWED_SLUGS.append('not')
        o = Project(slug='outsourced')
        o.name = "Dont'w want"
        o.outsource = pr
        o.save()
        g = Gtranslate.objects.get(project=o)
        self.assertFalse(g.use_gtranslate)
        p = Project(slug='ok')
        p.name = "Wants"
        p.save()
        g = Gtranslate.objects.get(project=p)
        self.assertTrue(g.use_gtranslate)


