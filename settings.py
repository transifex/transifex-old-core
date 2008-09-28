# Django settings for txc project.

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG
STATIC_SERVE = True

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

ADMINS = (
    ('Dimitris Glezos', 'dimitris@glezos.com'),
)

MANAGERS = ADMINS

# External app configuration

# Tagging
FORCE_LOWERCASE_TAGS = True

# Sites
SITE_ID = 1
SITE_NAME = 'Transifex'

# Email sending
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = 'admin@%s' % SITE_NAME

# Registration - OpenID
ugettext = lambda s: s
LOGIN_URL = '/%s%s' % ('account/', 'signin/')


# Database configuration

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'txc.db.sqlite'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Athens'

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
MEDIA_URL = '/site_media'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '89&f-)wka1gld*qr%pzt0uz%jmqc=0pttgv-_a&1(auvapj+d@'

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
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'django_authopenid.middleware.OpenIDMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.markup',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admindocs',
    'django_evolution',
    'django_authopenid',
    'transifex',    
    'tagging',
    'pagination',
    'contact_form',
    # txo specific apps:
    'vcs',
    'statistics',
    'projects',
    #'management',
)

####################
# vcs application settings

# The directory where the vcs app will checkout stuff and play around.
# Warning: On production systems this should be a place outside of the source
# and with enough disk space. Eg. /var/lib/transifex.
SCRATCH_DIR = os.path.join(PROJECT_PATH, 'scratchdir')

# Directories where checked-out units will be put.
REPOSITORIES_PATH = os.path.join(SCRATCH_DIR, 'sources')
# Per-VCS checkout directories, in case an override is required. The final
# location of a unit will be something like: SCRATCH_DIR/sources/hg/unit_slug.
HG_REPO_PATH = os.path.join(REPOSITORIES_PATH, 'hg')
SVN_REPO_PATH = os.path.join(REPOSITORIES_PATH, 'svn')
GIT_REPO_PATH = os.path.join(REPOSITORIES_PATH, 'git')

# Our VCS choices. This feeds the Unit model with the available options.
VCS_CHOICES = {#'bzr': 'Bazaar'
               #'cvs': 'CVS',
               'hg': 'Mercurial',
               'git': 'git',
               'svn': 'Subversion',}

# The classes which implement the VCS support. The full "path" to the class
# is the concatenation of the BASE and the NAME of the class.
BROWSER_CLASS_BASE = 'vcs.lib.types'
BROWSER_CLASS_NAMES = {#'bzr': 'bzr.BzrBrowser',
                       #'cvs': 'cvs.CvsBrowser',
                       'hg': 'hg.HgBrowser',
                       'git': 'git.GitBrowser',
                       'svn': 'svn.SvnBrowser',}

# Default submit message format for centralized VCSs. Backends can override
# this.
CVCS_SUBMIT_MSG = """%(date)s  %(userinfo)s

%(message)s"""

# Default submit message format for decentralized VCSs. Backends can override
# this.
DVCS_SUBMIT_MSG = """%(message)s
            
Transmitted-via: Transifex (%(domain)s)"""