import os
from django.conf import settings
from django.db.models.loading import get_model
from django.test import TestCase

from transifex.resources.models import RLStats
from transifex.txcommon.tests.base import BaseTestCase

Copyright = get_model('Copyright')


class CopyrightAppTests(BaseTestCase):
    def test_model(self):
        """Test model methods and attributes."""
        owner = str(self.user['registered'])
        from IPython.Shell import IPShellEmbed; ipython = IPShellEmbed()()
        cr = Copyright.objects.create(
            tresource=self.rls_en, owner='John Doe', year=2014)
        self.assertEqual(cr, "Copyright (C) 2014 John Doe")
        
        # create copyright
        # test copyright text
        # update copyright with next year
        # test copyright text

    def copyright_text_load(self):
        """Test the conversion of a copyright text to db objects."""
        sample_text = "Copyright (C) 2007-2010 Indifex Ltd."
        # load sample text
        # test db objects
        
    def poheader_load_sourclang_test(self):
        """Test load of existing PO file with copyright headers."""        

        test_file = os.path.join(settings.PROJECT_PATH,
                                 './resources/tests/lib/pofile/tests.pot'
        handler = POHandler(test_file)
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)

    def poheader_load_test(self):
        raise NotImplementedError
        
    def poheader_update_test(self):
        """Test load of existing PO file with copyright headers."""        

        test_file = os.path.join(settings.PROJECT_PATH,
                                 './resources/tests/lib/pofile/tests.pot'
        handler = POHandler(test_file)
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)

