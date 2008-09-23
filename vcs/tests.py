import unittest
from vcs.models import Unit, Repository

class UnitTestCase(unittest.TestCase):
    def setUp(self):
        r = Repository.objects.create(slug='foorepo', name='Foo',
                                      root='/home/mits/devel/txc/')
        self.unit = Unit.objects.create(repository=r, slug="foounit",
                                        name="Foo", directory='txc')

    def testBrowser(self):
        self.assertNotEqual(self.unit.directory, None)
        self.assertNotEqual(self.unit.repository.root, None)
        self.unit.init_browser()
        self.assertNotEqual(self.unit.browser, None)
        self.unit.browser.init_repo()
        self.unit.browser.update()