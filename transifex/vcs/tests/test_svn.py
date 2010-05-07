import commands
import os
import unittest
from vcs.models import VcsUnit

class SvnTestCase(unittest.TestCase):
    """Test Subversion VCS support.
    
    Supplementary tests, in addition to doctests.   
    """

    #TODO: Run the init stuff only when needed.
    def setUp(self):

        self.root = '%s/test_repo/svn/' % os.path.split(__file__)[0]
        #we need to remove any old checkout dir in order for it to exists within
        # our local paths
        try:
            os.unlink('%scheckout' % self.root)
        except OSError:
            pass
        #now recreate this within to create all the necessary local paths
        stat = commands.getstatusoutput('svn co file://%s/svnrepo/ %scheckout'
            % (self.root, self.root))
        self.unit = VcsUnit.objects.create(
            name="Test-SVN",
            root='%scheckout' % self.root,
            branch='trunk', type='svn')
        self.unit._init_browser()
        self.unit.browser.setup_repo()
        self.unit.browser.update()  
        
    def tearDown(self):
        self.unit.browser.teardown_repo()
        self.unit.delete()
        
    def test_repo_init(self):
        """Test correct SVN repo initialization."""
        from os import path
        from vcs.lib.types.svn import REPO_PATH 
        local_unit_path = path.join(REPO_PATH, self.unit.name)
        self.assertTrue(path.isdir(local_unit_path))

    def test_get_file_contents(self):
        """Test that SVN get_file_contents returns correct file size."""
        #FIXME: This is not the best way to test something like this!
        self.assertEquals(len(self.unit.browser.get_file_contents(
            'po/test_repo.pot')), 594)
