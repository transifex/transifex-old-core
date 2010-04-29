# -*- coding: utf-8 -*-
import unittest
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.client import Client
from projects.models import Project, Component

class TestCharts(unittest.TestCase):
    def test_main(self):
        c = Client()
        
        # Create a project
        project, created = Project.objects.get_or_create(slug="foo", name="Foo")
        component, created = Component.objects.get_or_create(slug="default", name="Default", project=project)

        # Check if widgets page is available
        resp = c.get(reverse('project_widgets', args = [project.slug]))
        self.assertEqual(resp.status_code, 200)

        # Check if django-staticfiles is serving widgets CSS
        resp = c.get("%swidgets/css/widgets.css" % settings.STATIC_URL, follow = True)
        self.assertEqual(resp.status_code, 200, msg = "Please run ./manage.py build_static")

        # Check if we got correct file
        self.assertTrue("code_snippet" in resp.content)