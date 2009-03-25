# Django settings for Transifex.
#
# PREFER TO OVERRIDE ANY OPTIONS IN settings_local.py
#
# It helps keeping this file clean with the default values
# and up to date with newer versions.

import os
import logging

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

# The following are usually overridden in settings_local.py
DEBUG = True
TEMPLATE_DEBUG = DEBUG
STATIC_SERVE = True

# Logging level/verbosity.
# Choices: logging.DEBUG (default), .INFO, .WARNING, .ERROR, .CRITICAL
LOG_LEVEL = logging.INFO


###########
# Management

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

SEND_BROKEN_LINK_EMAILS=True
MANAGERS = ADMINS

# Used when emailing managers and admins
EMAIL_SUBJECT_PREFIX = '[Transifex] '

###########
# External app configuration

# Tagging
FORCE_LOWERCASE_TAGS = True

# Sites
SITE_ID = 1
# Your site's domain. This is used only in this file.
SITE_DOMAIN = 'localhost'

# Email sending
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = 'admin@%s' % SITE_DOMAIN

# Notifications
# Enable notifications (requires working email settings)
# TODO: Make notifications not crash the app if email sending doesn't work.
# To enable notices you also need to enable the context processor and
# application below.
ENABLE_NOTICES = False

# Registration - OpenID
# Requires respective middleware and application
ENABLE_OPENID=True
ugettext = lambda s: s
LOGIN_URL = '/%s%s' % ('account/', 'signin/')


# Database configuration

DATABASE_ENGINE = 'sqlite3'                             # 'postgresql', ...
DATABASE_NAME = os.path.join(PROJECT_PATH, 'transifex.db.sqlite')  # Use file path for sqlite3
# The following are not used for sqlite3
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''             # Set to empty string for localhost.
DATABASE_PORT = ''             # Set to empty string for default.

# Enabling caching
# CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
# CACHE_MIDDLEWARE_SECONDS = 3600
# CACHE_MIDDLEWARE_KEY_PREFIX = 'txn'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Other/UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'site_media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
# NOTE: Also, this is hard-coded in the base.html template, so that the 500
# error page works. You'll need to change the occurences in that file too.
MEDIA_URL = '/site_media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = r"[[SECRETKEY]]"

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    # Notification support (requires app below too)
    # "notification.context_processors.notification",
)

MIDDLEWARE_CLASSES = [
    # Enable GZIP compression
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Enable protection against Cross Site Request Forgeries
    # Django 1.0.2's CSRF middleware doesn't have enough functionality,
    # so we pulled from Django dev
    'external.csrf.middleware.CsrfMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'pagination.middleware.PaginationMiddleware',
    # OpenID support (requires app below too)
    'django_authopenid.middleware.OpenIDMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.markup',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admindocs',
    # Notification support (requires context processor above too)
    # 'notification',
    # OpenId support (needs middleware class above too)
    'django_authopenid',
    'tagging',
    'pagination',
    'contact_form',
    # Transifex specific apps:
    'txcommon',
    'vcs',
    'translations',
    'languages',
    'projects',
    'txcollections',
    'releases',
    'actionlog',
    'simplelock',
    'repowatch',
]

####################
# vcs application settings

# The directory where the vcs app will checkout stuff and play around.
# Warning: On production systems this should be a place outside of the source
# and with enough disk space. Eg. /var/lib/transifex.
SCRATCH_DIR = os.path.join('/var/lib/transifex', 'scratchdir')

# The following settings define the VCS choices for the system.
# They are separated in basic and additional options below.

# BASIC VCS OPTIONS

# List of VCS types. Also feeds the Unit model with the available options.
VCS_CHOICES = {'hg': 'Mercurial',}

# Directories where checked-out units will be put. The final location of
# a unit will be something like: SCRATCH_DIR/sources/hg/unit_slug.
REPO_PATHS = {'hg': os.path.join(SCRATCH_DIR, 'sources', 'hg'),}

# The classes which implement the VCS support.
BROWSER_CLASS_NAMES = {'hg': 'vcs.lib.types.hg.HgBrowser',}

# Default submit message format for centralized VCSs. Backends can override
# this.
CVCS_SUBMIT_MSG = """%(date)s  %(userinfo)s

%(message)s"""

# Default submit message format for decentralized VCSs. Backends can override
# this.
DVCS_SUBMIT_MSG = """%(message)s

Transmitted-via: Transifex (%(domain)s)"""

####################
# TransHandler settings

# Our Translation Handler choices.
TRANS_CHOICES = {'POT': 'POT files',
                 'INTLTOOL': 'POT files using intltool',}

# The classes which implement the TransHandler support. The full "path"
# to the class is the concatenation of the BASE and the NAME of the class.
TRANS_CLASS_BASE = 'projects.handlers.types'
TRANS_CLASS_NAMES = {'POT': 'pot.POTHandler',
                     'INTLTOOL': 'intltool.IntltoolHandler',}

#####################
# msgmerge settings
MSGMERGE_DIR = os.path.join(SCRATCH_DIR, 'msgmerge_files')

# Enable msgfmt -c check for submission file
MSGFMT_CHECK = True

#####################
# ADDITIONAL VCS OPTIONS

VCS_CHOICES.update({'bzr': 'Bazaar',
                    'cvs': 'CVS',
                    'git': 'Git',
                    'svn': 'Subversion',})

REPO_PATHS.update({'bzr': os.path.join(SCRATCH_DIR, 'sources', 'bzr'),
                   'cvs': os.path.join(SCRATCH_DIR, 'sources', 'cvs'),
                   'git': os.path.join(SCRATCH_DIR, 'sources', 'git'),
                   'svn': os.path.join(SCRATCH_DIR, 'sources', 'svn'),})

BROWSER_CLASS_NAMES.update({'bzr': 'vcs.lib.types.bzr.BzrBrowser',
                            'cvs': 'vcs.lib.types.cvs.CvsBrowser',
                            'git': 'vcs.lib.types.git.GitBrowser',
                            'svn': 'vcs.lib.types.svn.SvnBrowser',})

# EXTRA LOCAL SETTINGS

# Put any settings specific to the particular host in settings_local.py

QUIT_ON_LOCAL_LOAD_FAILURE = True

import sys
import traceback

try:
    _localsettings = os.path.join(PROJECT_PATH, 'settings_local.py')
    if os.path.exists(_localsettings):
        execfile(_localsettings)
except StandardError, e:
    print >> sys.stderr, 'Unable to load local settings: %r' % (e,)
    print >> sys.stderr, 'Full traceback:'
    traceback.print_exc(file=sys.stderr)
    if QUIT_ON_LOCAL_LOAD_FAILURE:
        sys.exit(1)
del _localsettings
