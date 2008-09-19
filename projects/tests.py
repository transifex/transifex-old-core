import unittest

class SmokeTestCase(unittest.TestCase):
    #TODO: Run this for all applications, somehow
    #TODO: More customization: 404s, etc 
    #TODO: Make this run automatic for all 

    def setUp(self):
        self.pages = [
            '/projects/',
            '/projects/add/',
            '/projects/feeds/latest/',
#            '/search/',
#            '/search/?q=foo',
#            '/contact/',
#            '/account/',
#            '/',
        ]

    def testStatusCode(self):
        from django.test.client import Client
        client = Client()
        for page in self.pages:
            status_code = client.get(page).status_code
            self.assertEquals(status_code, 200,
                "Status code for page '%s' was %s instead of 200" %
                (page, status_code))
