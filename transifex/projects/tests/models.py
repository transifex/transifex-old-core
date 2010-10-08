# -*- coding: utf-8 -*-
from django.db import IntegrityError
from transifex.txcommon.tests.base import BaseTestCase
from transifex.languages.models import Language
from transifex.resources.models import Translation
from transifex.projects.models import Project


class ModelTests(BaseTestCase):
    
    def setUp(self):
        super(ModelTests, self).setUp()

    def tearDown(self):
        super(ModelTests, self).tearDown()

    def test_project_slug_integrity(self):
        """ Check duplication of project slug."""
        p, created = Project.objects.get_or_create(slug="foo",
                                                   name="Foo Project")
        new_p = Project(slug="foo", name="Foo Project")
        self.assertRaises(IntegrityError, new_p.save)

    def test_project_number_of_languages(self):
        """Test project available translated langs."""
        self.assertEqual(self.project.available_languages,
            Language.objects.filter(
                id__in=Translation.objects.filter(
          source_entity__resource__in=self.project.resources.all()).values_list(
              'language', flat=True).distinct()).distinct())