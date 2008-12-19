from django.conf import settings
"""
Local settings for the project.

These settings complement (and override) those in ``settings.py``,
by importing them at the end of the file. This means they also
appear as if they were defined there.
"""

# Email sending
#EMAIL_HOST = ''
#EMAIL_HOST_USER = ''
#EMAIL_HOST_PASSWORD = ''
#EMAIL_USE_TLS = True
#EMAIL_PORT = 587

#SCRATCH_DIR = os.path.join('/tmp', 'scratchdir')

from settings import *

# To enable the use of the notification app on your system:
#ENABLE_NOTICES = True
INSTALLED_APPS += ['django_evolution',]

#MIDDLEWARE_CLASSES += ['txn_stats.middleware.Activity']
#TEMPLATE_CONTEXT_PROCESSORS += ["notification.context_processors.notification",]
