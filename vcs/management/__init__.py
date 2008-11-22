import os
from django.conf import settings
import logging

# Check if vcs repositories are write-accessible.
for vcs in settings.VCS_CHOICES.keys():
    repo_path = settings.REPO_PATHS[vcs]
    if not os.path.isdir(repo_path):
        logging.error('Needed directory %s does not exist. Please create it.' %
                      repo_path)
    if not os.access(repo_path, os.W_OK):
        logging.error('Directory %s needs to be write-accessible.' % repo_path)
