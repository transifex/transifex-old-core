import unittest

class SmokeTestCase(unittest.TestCase):
    """Test that all project URLs return correct status code."""
    #TODO: Run this for all applications, somehow
    #TODO: More customization: 404s, etc 
    #TODO: Make this run automatic for all 

    def setUp(self):
        self.pages = {
            200: [
                '/projects/',
                '/projects/add/',
                '/projects/feeds/latest/',
                '/search/',
                # FIXME: Enable the following:
                # '/search/?q=a',
                '/contact/',
                '/account/signin/',
                '/account/signup/',
                '/account/sendpw/',],
            404: [
                '/foob4r/',
                '/projects/foob4r/',
                '/projects/feeds/foob4r/',
                '/account/foob4r/',]}

    def testStatusCode(self):
        from django.test.client import Client
        client = Client()
        for expected_code in self.pages.keys():
            for page_url in self.pages[expected_code]:
                page = client.get(page_url)
                self.assertEquals(page.status_code, expected_code,
                    "Status code for page '%s' was %s instead of %s" %
                    (page_url, page.status_code, expected_code))
