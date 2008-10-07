from django.conf import settings
"""
Local settings for the project.

These settings complement (and override) those in ``settings.py``.
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
#INSTALLED_APPS += ('notification',)
#TEMPLATE_CONTEXT_PROCESSORS += ("notification.context_processors.notification",)

# Note: Operator '-=' doesn't work on tuples :-(