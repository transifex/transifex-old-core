# -*- coding: utf-8 -*-
import polib, os

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from languages.models import Language
from languages.management.commands import txlanguages
from projects.models import Project
from resources.models import SourceEntity, Resource, TranslationString

# Uncomment out when you want to use the ipyhotn
#from IPython.Shell import IPShellEmbed
#ipython = IPShellEmbed()

# Sample file paths used in the tests
BASE_SAMPLE_FILE_PATH = os.path.join(settings.PROJECT_PATH,
                                     'resources/tests/sample_files')
SOURCE_PO = 'source_en.po'
# One less source string
SOURCE_PO_2 = 'source_en_2.po'
# Three more source strings
SOURCE_PO_3 = 'source_en_3.po'
# 10 more and 3 less source strings
SOURCE_PO_4 = 'source_en_4.po'

# Global vars
SOURCE_LANG = 'en'
TRESOURCE_BASE_NAME = 'test_resource'

class LoadingGettextTests(TestCase):
    """
    Test the loading process of PO/POT file data in the MongoDB.
    """

    def setUp(self):
        # Fill in the Test DB with all the languages.
        command = txlanguages.Command()
        command.run_from_argv(argv=["", ""])
        
        # Create a sample user
        if not getattr(self, 'user', None):
            self.user = User.objects.create_user('sl_user','test@local_test.org',
                                                 'sl_user')
        # Create a sample project
        self.project, created = Project.objects.get_or_create(slug='sl_project',
                                                              name='SL Project',
                                                              private=False,
                                                              owner=self.user)
        if created:
            self.project.maintainers.add(self.user)

        path_to_file = os.path.join(BASE_SAMPLE_FILE_PATH, SOURCE_PO)
        source_language = Language.objects.by_code_or_alias(code=SOURCE_LANG)
        name = TRESOURCE_BASE_NAME
        # Get a new tres
        self.tres = Resource.objects.create_from_file(path_to_file=path_to_file,
                        project=self.project,
                        source_language=source_language,
                        name=name)

    def tearDown(self):
        # Delete the Resource so we apply the updates on the original one!
        self.tres.delete()

    def test_source_po_loading(self):
        """
        Test that a sample po file of the source language is loaded correctly.
        
        Compare the entries of the po file with the entries stored in the db.
        """
        path_to_file = os.path.join(BASE_SAMPLE_FILE_PATH, SOURCE_PO)

        source_strings = SourceEntity.objects.filter(resource=self.tres)
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
            self.assertEqual(si.context, msgctxt)
#            self.assertEqual(si.developer_comment, entry.comment)
#            self.assertEqual(si.occurrences, entry.occurrences)
#            self.assertEqual(si.flags, entry.flags)


    def test_source_po_update_less(self):
        """
        Test that a sample po file of the source language is updated correctly.
        
        Compare the entries of the po file with the entries stored in the db.
        The new source pofile is has one entry deleted comparing it with the 
        previous!
        """
        path_to_file = os.path.join(BASE_SAMPLE_FILE_PATH, SOURCE_PO_2)

        # Now test the update of the same Resource source strings
        # (One less source string)
        self.tres.update_from_file(path_to_file=path_to_file, format='gettext')
        source_strings = SourceEntity.objects.filter(resource=self.tres, 
                                                     position__isnull=False)
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
            self.assertEqual(si.context, msgctxt)
#            self.assertEqual(si.developer_comment, entry.comment)
#            self.assertEqual(si.occurrences, entry.occurrences)
#            self.assertEqual(si.flags, entry.flags)

        # Check that there is one source string with position=None that belongs
        # to the same Resource (it is the historical one :))
        self.assertEqual(len(SourceEntity.objects.filter(resource=self.tres, 
                             position__isnull=True)), 1)

    def test_source_po_update_more(self):
        """
        Test an update on source file with more entries.
        """
        path_to_file = os.path.join(BASE_SAMPLE_FILE_PATH, SOURCE_PO_3)

        # Now test the update of the same Resource source strings
        # (One less source string)
        self.tres.update_from_file(path_to_file=path_to_file, format='gettext')
        source_strings = SourceEntity.objects.filter(resource=self.tres, 
                            position__isnull=False).order_by('position')
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
            self.assertEqual(si.context, msgctxt)
#            self.assertEqual(si.developer_comment, entry.comment)
#            self.assertEqual(si.occurrences, entry.occurrences)
#            self.assertEqual(si.flags, entry.flags)

        # Check that there is one source string with position=None that belongs
        # to the same Resource (it is the historical one :))
        self.assertEqual(len(SourceEntity.objects.filter(resource=self.tres, 
                             position__isnull=True)), 0)

    def test_source_po_update_mix(self):
        """
        Test an update on source file with more entries.
        """
        path_to_file = os.path.join(BASE_SAMPLE_FILE_PATH, SOURCE_PO_4)

        # Now test the update of the same Resource source strings
        # (One less source string)
        self.tres.update_from_file(path_to_file=path_to_file, format='gettext')
        source_strings = SourceEntity.objects.filter(resource=self.tres, 
                            position__isnull=False).order_by('position')
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
            self.assertEqual(si.context, msgctxt)
#            self.assertEqual(si.developer_comment, entry.comment)
#            self.assertEqual(si.occurrences, entry.occurrences)
#            self.assertEqual(si.flags, entry.flags)

        # Check that there are 3 source string with position=None that belongs
        # to the same Resource (it is the historical ones :))
        self.assertEqual(len(SourceEntity.objects.filter(resource=self.tres, 
                             position__isnull=True)), 3)
