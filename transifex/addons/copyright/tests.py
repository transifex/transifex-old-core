import os
from django.conf import settings
from django.db.models.loading import get_model
from django.test import TestCase

from transifex.languages.models import Language
from transifex.resources.models import Resource
from transifex.resources.formats.pofile import POHandler
from transifex.txcommon.tests.base import BaseTestCase

Copyright = get_model('copyright', 'Copyright')

class CopyrightTests(BaseTestCase):

    def test_manager(self):
        """Test manager's methods and attributes."""

        # Create basic copyright
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='John Doe', year='2014')
        self.assertEqual(str(cr), "John Doe, 2014.")

        # Test existing copyright
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='John Doe', year='2014')
        self.assertEqual(str(cr), "John Doe, 2014.")

        # Create consecutive copyright year
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='John Doe', year='2015')
        self.assertEqual(str(cr), "John Doe, 2014, 2015.")

        # Create non-consecutive copyright year
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='John Doe', year='2018')
        self.assertEqual(str(cr), "John Doe, 2014, 2015, 2018.")

        # Create another copyright holder
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='Django Reinhardt', year='2010')
        self.assertEqual(str(cr), "Django Reinhardt, 2010.")


    def copyright_text_load(self):
        """Test the conversion of a copyright text to db objects."""
        sample_text = "Copyright (C) 2007-2010 Indifex Ltd."
        # load sample text
        # test db objects

    def test_poheader_load_soureclang(self):
        """Test load of existing PO file with copyright headers."""

        test_file = os.path.join(settings.PROJECT_PATH,
                                 './resources/tests/lib/pofile/copyright.po')
        handler = POHandler(test_file)
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)
        c = Copyright.objects.filter(
            resource=self.resource, language=self.resource.source_language
        )
        self.assertEquals(len(c), 3)

    def poheader_load_test(self):
        raise NotImplementedError

    def poheader_update_test(self):
        """Test load of existing PO file with copyright headers."""
        raise NotImplementedError
