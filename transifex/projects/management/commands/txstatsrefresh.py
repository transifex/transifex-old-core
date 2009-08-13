from exceptions import Exception
import logging
import os
import traceback
from optparse import make_option, OptionParser
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import (LabelCommand, CommandError)
from projects.models import (Project, Component)

_HELP_TEXT = """Refresh translation statistics of registered components.

Use component full names (project_name.component_name) or
none to refresh all registered components.

Example::

    python manage.py txstatsrefresh fooproject.HEAD"""


RESUME_FILENAME = '.txstatsrefresh_resume.temp'

class Command(LabelCommand):
    """Refresh translation statistics of registered components."""
    option_list = LabelCommand.option_list + (
        make_option('--continue', action='store_true',
                    dest='continue', default=False,
            help='Try resuming operation from temporary progress file.'),
        make_option('--skip-broken', action='store_true',
                    dest='skip', default=False,
            help='Be more verbose in reporting progress.'),
        make_option('--verbose', action='store_true',
                    dest='verbose', default=False,
            help='Be more verbose in reporting progress.'),
    )
    help = (_HELP_TEXT)
           
    args = '[component component ...]'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False
    
    def handle(self, *comps, **options):
        """Override default method to make it work without arguments."""
        _continue = options.get('continue')
        skip = options.get('skip')
        verbose = options.get('verbose')
        if _continue and not os.access(os.path.dirname(__file__), os.W_OK):
            raise CommandError("Insufficient rights to resume file.")
            
        # If component not defined, get all of them.
        if not comps:
            comps = [c.full_name for c in Component.objects.all()]

        resume_list = []
        if _continue and os.path.exists(RESUME_FILENAME):
            try:
                # Read resume list
                readlog = open(RESUME_FILENAME, 'r')
                resume_list = readlog.readlines()
                readlog.close()
            except:
                # File isn't there (or something else anyway)
                pass
        if _continue:
            log = open(RESUME_FILENAME, 'a')

        errors = {}
        print 'Refreshing translation statistics...'
        try:
            for i, comp in enumerate(comps):
                if _continue and '%s\n' % comp in resume_list: # Note newline
                    print '%s/%s: Skipping\t%s' % (i+1, len(comps), comp)
                    continue
                print '%s/%s: Refreshing\t%s' % (i+1, len(comps), comp)
                try:
                    self.handle_label(comp, **options)
                except Exception, e:
                    logging.exception("Failed refreshing stats for %s." % comp)
                    errors[comp] = True
                    if skip:
                        print("Failed refreshing %s." % comp)
                        pass
                    else:
                        if verbose:
                            print traceback.format_exc()
                        raise CommandError("Error refreshing stats for %s. "
                            "Use --skip to ignore broken ones)." % comp)
                if _continue and not errors.has_key(comp):
                    log.write('%s\n' % comp)
        finally:
            if _continue:
                log.close()
        # When finished, resume file not needed.
        if _continue and len(errors) == 0:
            os.remove(RESUME_FILENAME)
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
        
        if comp.should_calculate:
            comp.prepare()
            # Calculate statistics
            try:
                comp.trans.set_stats()
            except:
                raise CommandError("Error in setting stats for %s." % comp.full_name)
                sys.stderr.write(self.style.ERROR(str('Error: %s\n' % e)))
                sys.exit(1)
        else:
            print "Statistics calculation is disabled for the particular component."