# -*- coding: utf-8 -*-

from django.conf import settings
from transifex.txcommon.tests.base import BaseTestCase
from transifex.projects.models import Project
from handlers import *
from models import Gtranslate
from transifex.addons.gtranslate import is_gtranslate_allowed

class TestGtranslate(BaseTestCase):

    def test_is_allowed(self):
        """Test if gtranslate is allowed for a particular project."""
        outp = Project.objects.create(slug='outsourced', name='outsourced')
        self.assertTrue(is_gtranslate_allowed(self.project))
        Gtranslate.objects.create(use_gtranslate=True, project=self.project)
        self.assertTrue(is_gtranslate_allowed(self.project))
        self.project.outsource = outp
        self.project.save()
        self.assertTrue(is_gtranslate_allowed(self.project))
        Gtranslate.objects.create(use_gtranslate=True, project=outp)
        self.assertTrue(is_gtranslate_allowed(self.project))

    def test_is_not_allowed(self):
        """Test if gtranslate is not allowed for a particular project."""
        outp = Project.objects.create(slug='outsource', name='outsource')
        g = Gtranslate.objects.create(use_gtranslate=False, project=self.project)
        self.assertFalse(is_gtranslate_allowed(self.project))
        self.project.outsource = outp
        self.project.save()
        self.assertFalse(is_gtranslate_allowed(self.project))
        Gtranslate.objects.create(use_gtranslate=False, project=outp)
        self.assertFalse(is_gtranslate_allowed(self.project))
        g1 = Gtranslate.objects.get(project=outp)
        g1.use_gtranslate=True
        g1.save()
        self.assertFalse(is_gtranslate_allowed(self.project))
        g.use_translate = True
        g.save()
        g1.use_translate = False
        g1.save()
        self.assertFalse(is_gtranslate_allowed(self.project))

    def test_delete(self):
        """Test, if a gtranslate entry is deleted, when the corresponding
        project is delete.
        """
        p = Project(slug="rm")
        p.name = "RM me"
        p.save()
        Gtranslate.objects.create(use_gtranslate=False, project=p)
        delete_gtranslate(p)

    def test_projects_not_in_gtranslate_table(self):
        """Test the number of projects which are not in Gtranslate table"""
        self.test_is_allowed()
        projects_list = []
        for p in Project.objects.all():
            try:
                Gtranslate.objects.get(project=p)
            except:
                projects_list.append(p)

        self.assertEqual(len(projects_list), 6)

    def test_default(self):
        """Test what happens when a project (or its outsource) are not
        in the gtranslate table.
        """
        self.assertTrue(is_gtranslate_allowed(self.project))
        outp = Project.objects.create(
            slug='outp', name='A new project'
        )
        self.project.outsource = outp
        self.project.save()
        self.assertTrue(is_gtranslate_allowed(self.project))

