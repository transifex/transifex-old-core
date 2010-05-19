import os
import unittest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from vcs.lib.exceptions import *
from vcs.lib.types.hg import REPO_PATH
from vcs.models import VcsUnit

class HgVCS(unittest.TestCase):
    """
    Test Hg VCS support.

    Supplementary tests, in addition to doctests.
    """
    def setUp(self):
        self.unittest_scratchdir = os.path.join(settings.SCRATCH_DIR, 
            'unittest/repos/')
        self.source_root = '%s/test_repo/hg' % os.path.split(__file__)[0]
        self.root = '%s/hg' % self.unittest_scratchdir
        os.system('mkdir -p %s; cd %s; cp -rf %s ./' % (
            self.unittest_scratchdir, self.unittest_scratchdir, 
            self.source_root))
        os.system('cd %s; hg init; hg add *; hg commit -m "Init repo"'
                  % self.root)

        self.unit = VcsUnit.objects.create(name="Test-HG", root=self.root,
            type='hg')
        self.unit._init_browser()
        self.unit.browser.setup_repo()

    def tearDown(self):
        self.unit.browser.teardown_repo()
        self.unit.delete()
        os.system('rm -rf %s' % self.root)

    def test_repo_init(self):
        """Test Hg repository initialization."""
        local_unit_path = os.path.join(REPO_PATH, self.unit.name)
        self.assertTrue(os.path.isdir(local_unit_path))

        self.unit.browser.teardown_repo()
        self.unit.root = '%s/norepo/' % self.unit.root
        self.unit._init_browser()

        # Trying to setup/checkout a non-existing repository
        self.assertRaises(SetupRepoError, self.unit.browser.setup_repo)

    def test_get_file_contents(self):
        """Test get_file_contents checking for the correct file size."""
        self.assertEquals(len(
            self.unit.browser.get_file_contents('po/test_repo.pot')), 594)

    def test_get_revision(self):
        """Test get_rev output."""
        # Get revision for existing file. It must be a tuple.
        self.assertEquals(type(self.unit.browser.get_rev('po/pt_BR.po')), 
            tuple)

        # Get revision for non-existing file
        self.assertRaises(RevisionRepoError, self.unit.browser.get_rev,
            'po/foo.po')

    def test_update(self):
        """Test repository update/pull."""
        # Pulling from an available repository
        self.assertTrue(self.unit.browser.update)

        os.system('rm -rf %s/.hg' % self.root)
        # Pulling from a non-existing/unavailable repository
        self.assertRaises(UpdateRepoError, self.unit.browser.update)

    def test_submit(self):
        """Test submission and pushing."""
        user, created = User.objects.get_or_create(username='unittest_user')
        filename = 'po/pt_BR.po'
        po_content = self.unit.browser.get_file_contents(filename)
        message = "Testing Submission"

        new_content = "#%s\n%s" % ( message, po_content)
        submitted_file = SimpleUploadedFile(filename, new_content)
        submitted_file.targetfile = filename
        file_dict = {'submitted_file':submitted_file}

        # Committing to the default branch
        self.unit.browser.submit(file_dict, message, user)

        # Commiting to a 'foo' branch that doesn't exist
        self.unit.branch = 'foo'
        self.unit._init_browser()
        self.assertRaises(PushRepoError, self.unit.browser.submit, file_dict,
            message, user)
