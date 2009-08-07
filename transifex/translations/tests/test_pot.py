import unittest
from vcs.models import VcsUnit
from projects.models import Project, Component
from translations.lib.types.pot import POTStatsError
from translations.lib.types.pot import POTManager

class POTTestCaseBase(unittest.TestCase):
    """Test POT support.
    
    Supplementary tests, in addition to doctests.   
    """

    #TODO: Run the init stuff only when needed.
    def setUp(self):

        # Creating a project
        self.p = Project.objects.create(slug="foo", name="Foo Project")
        self.p.save()

        # Creating a component with an unit
        self.c = Component(slug='bar', project=self.p, i18n_type='POT', 
                           file_filter='po/.*')

        # Creating an unit
        self.c.set_unit(branch='master', type='git',
                  root='git://git.fedorahosted.org/git/docs/readme.git')

        self.c.save()

        # Initializing the component's unit
        self.c.unit.init_browser()

        # Unit checkout
        self.c.unit.browser.init_repo()

        self.tm = POTManager(self.c.get_files(),
                             self.c.unit.browser.path, 
                             self.c.source_lang)

    def tearDown(self):
        self.c.unit.browser.teardown_repo()
        self.c.unit.delete()
        self.c.delete()
        self.p.delete()

class POTTestCase(POTTestCaseBase):

    def test_calcule_stats(self):
        """Test that tm.browser.calcule_stats works properly."""

        stats = self.tm.calcule_stats('pt_BR')
        self.assertTrue(len(stats)>0)

        try:
            stats = self.tm.calcule_stats('--')
        except POTStatsError:
            pass
        else:
            fail("expected a POTStatsError")

    def test_get_langs(self):
        """Test that tm.browser.get_langs works properly."""

        langs = self.tm.get_langs()
        self.assertTrue(len(langs)>0)

    def test_get_po_files(self):
        """Test that tm.browser.get_po_files works properly."""

        pofiles = self.tm.get_po_files()
        self.assertTrue(len(pofiles)>0)

    def test_get_langfile(self):
        """Test that tm.browser.get_langfile works properly."""

        file = self.tm.get_langfile('pt_BR')
        self.assertTrue(len(file)>0)
