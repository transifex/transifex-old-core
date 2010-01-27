import unittest
from projects.models import (Project, Release)

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


class ReleaseTest(unittest.TestCase):
#    fixtures = ['test-data.json']
    
    def setUp(self):
        pass
    
    def test_release(self):
        """
        Test relationships between releases and other elements.

        >>> from django.core.management import call_command
        >>> call_command('loaddata', 'projects/fixtures/test-data.json')
        Installing json fixture 'projects/fixtures/test-data' from absolute path.
        ...

        Test the release -> project relationship
        >>> p = Project.objects.get(slug='test') 
        >>> r = p.releases.get(slug='test-release')                
        
        Test the release -> project relationship
        >>> r = Release.objects.get(slug='test-release')
        >>> r.project
        <Project: Test Project>
        """
