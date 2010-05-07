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
        self.project, created = Project.objects.get_or_create(
            slug="test_project_lang", name="Test Project Langs")
        self.component, created = Component.objects.get_or_create(
            slug='test_component_lang', project=self.project, i18n_type='POT',
            file_filter='po/.*', name='Test Component Langs')

        # Creating a component with an unit
        self.reporoot = 'git://git.fedorahosted.org/git/desktop-effects.git'
        # Creating an unit
        try:
            self.component.unit = VcsUnit.objects.get(name=self.component.full_name)
            self.component.save()
        except:
            self.component.set_unit(branch='master', type='git', root=self.reporoot)


        # Initializing the component's unit
        self.component.unit._init_browser()

        # Unit checkout
        self.component.prepare()

    def tearDown(self):
        self.component.unit.browser.teardown_repo()
        self.component.delete()
        self.project.delete()

class POTTestCase(POTTestCaseBase):

    def test_calcule_stats(self):
        """Test that tm.browser.calcule_stats works properly."""
        self.component.trans.set_stats()
        pofiles = self.component.trans.get_stats()
        for pofile in pofiles:
            self.assertEquals(pofile.fuzzy+pofile.trans+pofile.untrans,
                pofile.total)
        if self.component.trans.get_lang_stats('--'):
            fail('lala')

    def test_get_langs(self):
        """Test that tm.browser.get_langs works properly."""

        langs = self.component.trans.tm.get_langs()
        self.assertTrue(langs.next())

    def test_get_po_files(self):
        """Test that tm.browser.get_po_files works properly."""

        pofiles = self.component.trans.tm.get_po_files()

        self.assertTrue(pofiles.next())

    def test_get_langfile(self):
        """Test that tm.browser.get_langfile works properly."""

        file = self.component.trans.tm.get_lang_files('pt_BR')
        self.assertTrue(file.next())
