import os
import unittest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from vcs.lib.exceptions import *
from vcs.lib.types.svn import REPO_PATH 
from vcs.models import VcsUnit

class SvnVCS(unittest.TestCase):
    """Test Subversion VCS support.

    Supplementary tests, in addition to doctests.   
    """
    def setUp(self):
        # Temp location for the SVN testing repository
        self.unittest_scratchdir = os.path.join(settings.SCRATCH_DIR,
            'unittest/repos/svn/')

        # Path to the data that should be used to create the svn repo.
        self.repo_data = '%s/test_repo/svn' % os.path.split(__file__)[0]

        # Base repo path.
        self.svn_repo = '%srepo' % self.unittest_scratchdir

        # Root URL of the repo. Used in checkouts for example.
        self.root = 'file://%s/repo_data' % self.svn_repo

        os.system('mkdir -p %s' % self.unittest_scratchdir)

        # Creating a SVN repo and importing some data into a project repo.
        os.system("rm -rf %s" % self.svn_repo )
        os.system('svnadmin create %s' % self.svn_repo)
        os.system('svn import %s %s -m "Initial"' % (self.repo_data,
            self.root))

        # Enabling pre-revprop-change hook
        #hook_path = '%s/hooks/pre-revprop-change' % self.svn_repo
        #os.system('mv %s.tmpl %s' % (hook_path, hook_path))
        #os.system('chmod +x %s' % hook_path)

        self.unit = VcsUnit.objects.create(name="Test-SVN", root=self.root,
            branch='trunk', type='svn')
        self.unit._init_browser()
        self.unit.browser.setup_repo()

    def tearDown(self):
        self.unit.browser.teardown_repo()
        self.unit.delete()
        # Removing temp SVN repo
        os.system("rm -rf %s" % self.unittest_scratchdir )

    def test_repo_init(self):
        """Test Svn repo initialization."""
        local_unit_path = os.path.join(REPO_PATH, self.unit.name)
        self.assertTrue(os.path.isdir(local_unit_path))

        self.unit.browser.teardown_repo()
        self.unit.root = '%s/norepo/' % self.unit.root
        self.unit._init_browser()

        # Trying to setup/checkout a non-existing repository
        self.assertRaises(SetupRepoError, self.unit.browser.setup_repo)

    def test_get_file_contents(self):
        """Test get_file_contents checking for the correct file size."""
        self.assertEquals(len(self.unit.browser.get_file_contents(
            'po/test_repo.pot')), 594)

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
