# -*- coding: utf-8 -*-

"""
Client-version specific functions.
"""

from __future__ import absolute_import
from pkg_resources import parse_version
from .conf import LATEST_VERSION


def user_agent(request):
    """
    Return the User-Agent of a request.

    We only return the identifier, instead of the whole string.
    """
    agent_string = request.META.get('HTTP_USER_AGENT')
    if agent_string is not None:
        agent_string = agent_string.split(' ', 1)[0]
    return agent_string


def is_client_request(request):
    agent_string = user_agent(request)
    return agent_string.startswith('txclient')


def extract_version(user_agent):
    """
    Extract the version from the User-Agent header.

    We follow RFC 2616, section 14.43.
    """
    return user_agent.rsplit('/', 1)[1]


def is_client_old(version):
    return parse_version(version) < parse_version(LATEST_VERSION)
