import unittest
from vcs.models import Unit

class HgTestCase(unittest.TestCase):
    """Test Hg VCS support.
    
    Supplementary tests, in addition to doctests.   
    """ 

    #TODO: Run the init stuff only when needed.
    def setUp(self):
        self.unit = Unit.objects.create(
            name="Test-HG",
            root='http://code.transifex.org/transifex',
            branch='tip', type='hg')
    def tearDown(self):
        self.unit.delete()
        # Until we use a local repo, let's not delete it after the first run:
        # self.unit.browser.teardown_repo()

    def test_repo_init(self):
        """Test correct Hg repo initialization."""
        from os import path
        from vcs.lib.types.hg import HG_REPO_PATH 
        self.unit.init_browser()
        self.unit.browser.init_repo()
        local_unit_path = path.join(HG_REPO_PATH, self.unit.name)
        self.assertTrue(path.isdir(local_unit_path))

    def test_get_file_contents(self):
        """Test that Hg get_file_contents returns correct file size."""
        #FIXME: This is not the best way to test something like this!
        self.unit.init_browser()
        self.unit.browser.init_repo()
        self.assertEquals(len(self.unit.browser.get_file_contents('LICENSE')),
                          18018)
