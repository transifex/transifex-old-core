from __future__ import absolute_import
import re
from itertools import chain
from django.utils import unittest
from transifex.txcommon.tests.factories import RequestFactory
from .versions import user_agent, is_client_request, extract_version, \
        is_client_old
from .notify import _mail_already_sent, _cache_key, delete_from_cache


class TestVersion(unittest.TestCase):
    """Tests for handling client versions."""

    def setUp(self):
        self.client_agent_strings = [
            'txclient/0.7.2 (Linux x64)',
            'txclient/0.8 (Linux i386)',
        ]
        self.other_agent_strings = [
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64)',
            'Mozilla/5.0 (compatible; Googlebot/2.1)',
            'Opera/9.80 (Windows NT 6.1)',
            'AppleWebKit/535.19 (KHTML, like Gecko)',
        ]

    def test_user_agent_extration(self):
        """Test how we extract the user agent from a request."""
        request = RequestFactory()
        for agent in chain(self.client_agent_strings, self.other_agent_strings):
            request.META['HTTP_USER_AGENT'] = agent
            res = user_agent(request)
            self.assertIn(res, agent)
            self.assertNotIn('(', res)

    def test_detecting_client_requests(self):
        """Test the detection of a client request."""
        request = RequestFactory()
        for agent in self.client_agent_strings:
            request.META['HTTP_USER_AGENT'] = agent
            self.assertTrue(is_client_request(request))
        for agent in self.other_agent_strings:
            request.META['HTTP_USER_AGENT'] = agent
            self.assertFalse(is_client_request(request))

    def test_extracting_version(self):
        """Test the extraction of the version from a user agent string."""
        version_regex = re.compile(r'(\d|.)+$')
        for agent in chain(self.client_agent_strings, self.other_agent_strings):
            agent_string = agent.split(' ', 1)[0]
            version = extract_version(agent_string)
            self.assertIsNotNone(version_regex.match(version))

    def test_detecting_old_client(self):
        """Test the detection of old client versions."""
        versions = ['0.0.1', '0.0.2', '0.1a', ]
        for version in versions:
            self.assertTrue(is_client_old(version))
        versions = ['0.1', '0.2', '0.1.1', ]
        for version in versions:
            self.assertFalse(is_client_old(version))


class TestNotifications(unittest.TestCase):
    """Test mail notifications to users for using old clients."""

    def setUp(self):
        self.email = 'me@example.com'

    def tearDown(self):
        delete_from_cache(self.email)

    def test_already_sent_check(self):
        """Test detecting whether a notification has been sent or not."""
        self.assertFalse(_mail_already_sent(self.email))
        self.assertTrue(_mail_already_sent(self.email))
