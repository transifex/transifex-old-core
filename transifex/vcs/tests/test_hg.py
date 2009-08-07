import os
import unittest
from vcs.models import VcsUnit

class HgTestCase(unittest.TestCase):
    """Test Hg VCS support.
    
    Supplementary tests, in addition to doctests.   
    """

    #TODO: Run the init stuff only when needed.
    def setUp(self):
        self.root='%s/test_repo/hg' % os.path.split(__file__)[0]
        os.system('cd %s; hg init; hg add *; hg commit -m "Init repo"'
                  % self.root)
        self.unit = VcsUnit.objects.create(
            name="Test-HG",
            root=self.root,
            branch='tip', type='hg')
    def tearDown(self):
        self.unit.delete()
        os.system('rm -rf %s/.hg' % self.root)
        # Until we use a local repo, let's not delete it after the first run:
        # self.unit.browser.teardown_repo()

    def test_repo_init(self):
        """Test correct Hg repo initialization."""
        from os import path
        from vcs.lib.types.hg import REPO_PATH
        self.unit._init_browser()
        self.unit.browser.init_repo()
        local_unit_path = path.join(REPO_PATH, self.unit.name)
        self.assertTrue(path.isdir(local_unit_path))

    def test_get_file_contents(self):
        """Test that Hg get_file_contents returns correct file size."""
        #FIXME: This is not the best way to test something like this!
        self.unit._init_browser()
        self.unit.browser.init_repo()
        self.assertEquals(len(self.unit.browser.get_file_contents('po/test_repo.pot')),
                          594)
