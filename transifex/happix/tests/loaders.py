# -*- coding: utf-8 -*-
import polib, os

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from happix.models import SourceString, TResource, TranslationString, PluralTranslationString
from languages.models import Language
from languages.management.commands import txcreatelanguages
from projects.models import Project

# Uncomment out when you want to use the ipyhotn
#from IPython.Shell import IPShellEmbed
#ipython = IPShellEmbed()

# Sample file paths used in the tests
BASE_SAMPLE_FILE_PATH = os.path.join(settings.PROJECT_PATH,
                                     'happix/tests/sample_files')
SOURCE_PO = 'source_en.po'

# Global vars
SOURCE_LANG = 'en'
TRESOURCE_BASE_NAME = 'test_resource'

class LoadingGettextTests(TestCase):
    """
    Test the loading process of PO/POT file data in the MongoDB.
    """

    def setUp(self):
        # Fill in the Test DB with all the languages.
        command = txcreatelanguages.Command()
        command.run_from_argv(argv=["", ""])
        
        # Create a sample user
        self.user = User.objects.create_user('sl_user','test@local_test.org',
                                             'sl_user')
        # Create a sample project
        self.project = Project.objects.create(slug='sl_project',
                                              name='SL Project',
                                              private=False,
                                              owner=self.user)
        self.project.maintainers.add(self.user)

    def tearDown(self):
        self.user.delete()
        self.project.delete()

    def test_source_lang_po_loading(self):
        """
        Test that a sample po file of the source language is loaded correctly.
        
        Compare the entries of the po file with the entries stored in the db.
        """
        path_to_file = os.path.join(BASE_SAMPLE_FILE_PATH, SOURCE_PO)
        source_language = Language.objects.by_code_or_alias(code=SOURCE_LANG)
        name = TRESOURCE_BASE_NAME

        # Get a new tres
        tres = TResource.objects.create_from_file(path_to_file=path_to_file,
                                   project=self.project,
                                   source_language=source_language,
                                   name=name)

        source_strings = SourceString.objects.filter(tresource=tres)
        pofile = polib.pofile(path_to_file)

        # Check that source language strings in DB has the same len as the
        # number of msgids in the source lang file.
        self.assertEqual(len(source_strings), len(pofile))

        # Check one by one the DB entries that are the same with the file msgids
        for si, entry in zip(source_strings, pofile):
            self.assertEqual(si.string, entry.msgid)
            msgctxt = entry.msgctxt
            # CAUTION! MSGCTXT None is converted to empty string u'' in DB.
            if msgctxt == None:
                msgctxt = u''
            self.assertEqual(si.description, msgctxt)
#            self.assertEqual(si.developer_comment, entry.comment)
#            self.assertEqual(si.occurrences, entry.occurrences)
#            self.assertEqual(si.flags, entry.flags)
