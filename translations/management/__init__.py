import os
from django.conf import settings
import logging

MSGMERGE_DIR = settings.MSGMERGE_DIR

# Check if vcs repositories are write-accessible.
if not os.path.isdir(MSGMERGE_DIR):
    logging.error('Needed directory %s does not exist. Please create it.' %
                  MSGMERGE_DIR)
