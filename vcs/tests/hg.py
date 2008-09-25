import unittest
from vcs.models import Unit

class HgTestCase(unittest.TestCase):
    """Test Hg VCS support.""" 

    #TODO: Run the init stuff only when needed.
    def setUp(self):
        self.unit = Unit.objects.create(
            name="Foo", slug="testhg",
            root='http://code.transifex.org/transifex',
            branch='tip', type='hg')
    def tearDown(self):
        self.unit.delete()
        # Until we use a local repo, let's not delete it after the first run:
        # self.unit.browser.teardown_repo()

    def test_browser_init(self):
        """Test if browser was initialized correctly."""
        self.unit.init_browser()
        self.assertEqual(self.unit.browser.root, self.unit.root)

    def test_traversal_browser(self):
        """
        Test that weird models don't get a browser at all.
        
        Creating a local unit just for this purpose.
        """
        unit = Unit.objects.create(name="Trav", slug="../../trav",
                                        root='foo',
                                        branch='tip', type='hg')
        self.assertRaises(AssertionError, unit.init_browser)
        unit.delete()

    def test_repo_init(self):
        """Test correct repo initialization."""
        from os import path
        from vcs.lib.types.hg import HG_REPO_PATH 
        self.unit.init_browser()
        self.unit.browser.init_repo()
        local_unit_path = path.join(HG_REPO_PATH, self.unit.slug)
        self.assertTrue(path.isdir(local_unit_path))

    def test_get_file_contents(self):
        """Test that get_file_contents returns correct file size."""
        #FIXME: This is not the best way to test something like this!
        self.unit.init_browser()
        self.unit.browser.init_repo()
        self.assertEquals(len(self.unit.browser.get_file_contents('LICENSE')),
                          18018)
