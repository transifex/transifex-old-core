import os, settings, traceback
from optparse import make_option
from django.core.management.base import (BaseCommand, LabelCommand, CommandError)

from projects.models import Project
from txcommon.log import logger
from resources.loaders import load_dir_hierarchy

_HELP_TEXT = """Load Resources to the DB by parsing the scratchdir.

This is a dummy command, it uses the well known path for scratchdir and it 
automatically parses all the sources there, extracts the project names and 
fills the data in the db by creating the appropriate Resources, SourceStrings,
TranslationStrings.

Example:

    python manage.py load_from_scratchdir_dummy"""

SCRATCH_DIR = getattr(settings, 'SCRATCH_DIR', None)

class Command(BaseCommand):
    """The command class"""
    option_list = LabelCommand.option_list + (
        make_option('--verbose', action='store_true',
                    dest='verbose', default=False,
            help='Be more verbose in reporting progress.'),
    )

    help = (_HELP_TEXT)

    def handle(self, *comps, **options):
        """The command handler method"""
        verbose = options.get('verbose')

        if not SCRATCH_DIR:
            print ("Firstly, setup the SCRATCH_DIR parameter in settings and "
                   "then run again the command!")
            return

        BASE_SOURCES_DIR = os.path.join(SCRATCH_DIR, 'sources')

        # Get vcs types and fetch their scratchdir paths
        for short_type_name, type_name in settings.CODEBASE_CHOICES.items():

            parent_path = os.path.join(BASE_SOURCES_DIR, short_type_name)
            # Iterate through all repos of the specific vcs type
            for rel_path in os.listdir(parent_path):
                
                # If we care about project we should comment out the following
                #project_fullname = os.path.basename(path)

                path = os.path.join(parent_path, rel_path)
                print "Processing the following path: %s" % path
                # Project, Source language and name are given the defaults
                try:
                    load_dir_hierarchy(directory_path=path,
                                       project=None,
                                       source_language=None,
                                       name=None,
                                       format='gettext')
                except Exception, e:
                    logger.error("Failed loading path %s." % path)
                    print traceback.format_exc()
        print 'Done.'
