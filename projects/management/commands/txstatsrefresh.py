import logging
from optparse import make_option, OptionParser
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import (LabelCommand, CommandError)
from projects.models import (Project, Component)

_HELP_TEXT = """Refresh translation statistics of registered components.

Use component full names (project_name.component_name) or
none to refresh all registered components.

Example::

    python manage.py txstatsrefresh fooproject.HEAD"""

class Command(LabelCommand):
    option_list = LabelCommand.option_list + (
        make_option('--verbose', action='store_true', dest='verbose', default=False,
            help='Be more verbose in reporting progress.'),
    )
    help = (_HELP_TEXT)
           
    args = '[component component ...]'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False
    
    def handle(self, *comps, **options):
        """Override default method to make it work without arguments.""" 
        if not comps:
            comps = [c.full_name for c in Component.objects.all()]
           
        print 'Refreshing translation statistics...'
        for comp in comps:
            self.handle_label(comp, **options)
        print 'Done.'

    def handle_label(self, comp, **options):
        self.refresh_stats(comp_name = comp, **options)

    def refresh_stats(self, comp_name, **options):
        """Refresh the statistics of a component with full_name 'comp_name'."""
        verbose = options.get('verbose')
        try:
            comp = Component.objects.get(full_name=comp_name)
        except ObjectDoesNotExist:
            raise CommandError("No component with full name '%s'." % comp_name)
        if verbose:
            print '- %s' % (comp.full_name)
        comp.prepare_repo()
        # Calculate statistics
        try:
            comp.trans.set_stats()
        except e:
            raise CommandError("Error in setting stats for %s." % comp.full_name)
            sys.stderr.write(self.style.ERROR(str('Error: %s\n' % e)))
            sys.exit(1)
