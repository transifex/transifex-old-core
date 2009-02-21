import logging
from optparse import make_option, OptionParser
from django.conf import settings
from django.core.management.base import (BaseCommand, CommandError)
from projects.models import (Project, Component)

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noreload', action='store_false', dest='use_reloader', default=True,
            help='Tells Django to NOT use the auto-reloader.'),
    )
    help = "Starts a lightweight Web server for development."
    args = '[optional port number, or ipaddr:port]'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def handle(self, addrport='', *args, **options):
        import django
        for project in Project.objects.all():
            for component in project.component_set.all():
                print 'Calculating statistics for: %s' % (component.full_name)
                component.prepare_repo()
                # Calcule statistics
                try:
                    component.trans.set_stats()
                except e:
                    sys.stderr.write(self.style.ERROR(str('Error: %s\n' % e)))
                    sys.exit(1)
