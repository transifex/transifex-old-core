import os
import unittest
from txcommon.commands import (run_command, CommandError)
from vcs.lib.types.svn import REPO_PATH 
from vcs.models import VcsUnit

class SvnTestCase(unittest.TestCase):
    """Test Subversion VCS support.

    Supplementary tests, in addition to doctests.   
    """
    def setUp(self):
        # Base location of the SVN repo test stuff.
        base_path = '%s/test_repo/svn' % os.path.split(__file__)[0]

        # Base repo path.
        self.svn_repo = '%s/repo' % base_path

        # Path to the data that should be used to create the svn repo.
        self.repo_data = '%s/data' % base_path

        # Root URL of the repo. Used in checkouts for example.
        self.root = 'file://%s/repo_data' % self.svn_repo

        # Creating a SVN repo and importing some data into a project repo.
        run_command("rm -rf %s" % self.svn_repo )
        run_command('svnadmin create %s' % self.svn_repo)
        run_command('svn import %s %s -m "Initial"' % (self.repo_data,
            self.root))

        self.unit = VcsUnit.objects.create(name="Test-SVN", root=self.root,
            branch='trunk', type='svn')
        self.unit._init_browser()
        self.unit.browser.setup_repo()
        self.unit.browser.update()

    def tearDown(self):
        self.unit.browser.teardown_repo()
        self.unit.delete()
        # Removing temp SVN repo
        run_command("rm -rf %s" % self.svn_repo )

    def test_repo_init(self):
        """Test correct SVN repo initialization."""
        self.assertTrue(os.path.isdir(os.path.join(REPO_PATH, self.unit.name)))

    def test_get_file_contents(self):
        """Test that SVN get_file_contents returns correct file size."""
        self.assertEquals(len(self.unit.browser.get_file_contents(
            'po/test_repo.pot')), 594)
