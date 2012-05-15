# -*- coding: utf-8 -*-

"""
Configuration file for the app.
"""

from django.conf import settings

_DEFAULT_INTERVAL  = 30 * 24 * 60 * 60 # a month
# latest version of the client
LATEST_VERSION = getattr(settings, 'TXCLIENT_VERSION', '0.1')
INTERVAL = getattr(settings, 'TXCLIENT_NOTIFICATION_INTERVAL', _DEFAULT_INTERVAL)
