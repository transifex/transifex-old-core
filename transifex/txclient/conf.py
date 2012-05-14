# -*- coding: utf-8 -*-

"""
Configuration file for the app.
"""

from django.conf import settings


# latest version of the client
LATEST_VERSION = getattr(settings, 'CLIENT_VERSION', '0.1')
