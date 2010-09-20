import os, sys
from django.core.management.base import NoArgsCommand

def transifex_paths():
    from django.conf import settings as s
    # Scratch dir
    yield s.SCRATCH_DIR
    # Msgmerge dir
    yield s.STORAGE_DIR
    # Log path
    yield s.LOG_PATH


class Command(NoArgsCommand):
    help = 'Create required directories'

    requires_model_validation = True
    can_import_settings = True

    def handle_noargs(self, **options):
        for path in transifex_paths():
            try:
                os.makedirs(path)
                sys.stdout.write("Creating %s\n" % path)
            except OSError, e:
                sys.stdout.write("Error creating %s: %s\n" % (path, e.strerror))

