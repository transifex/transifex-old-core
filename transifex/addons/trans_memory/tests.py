from transifex.txcommon.tests.base import BaseTestCase

class MemoryViewsTests(BaseTestCase):

    def setUp(self):
        super(MemoryViewsTests, self).setUp()
        self.entity = self.resource.entities[0]
        self.URL_PREFIX = '/search_translations/'

    def testAnonymousPagesStatusCode(self):
        pages = {302: [(self.URL_PREFIX),],}
        self.assert_url_statuses(pages, self.client["anonymous"])

    def test_memory_search(self):
        raise NotImplementedError


    def test_private_project(self):
        """Test access to various methods if the project is private."""
        raise NotImplementedError

