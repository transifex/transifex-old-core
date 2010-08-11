from optparse import make_option
import traceback
from django.core.management.base import BaseCommand
from django.core.management.base import LabelCommand, CommandError

from projects.models import Project, Component
from txcommon.log import logger
from resources.loaders import load_dir_hierarchy

_HELP_TEXT = """Load Resources to the DB.

The paths are automatically retrieved from the legacy models Project, POFile etc.

Example:

    python manage.py load_from_scratchdir"""

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

        # Get Components and fetch their scratchdir paths
        for component in Component.objects.all():

            try:
                component.unit._init_browser()
                # Source language and name are given the defaults
                load_dir_hierarchy(directory_path=component.unit.browser.path,
                                   project=component.project,
                                   source_language=None,
                                   name=None,
                                   format='gettext')
            except Exception, e:
                logger.error("Failed loading component %s." % component)
                print traceback.format_exc()
        print 'Done.'
