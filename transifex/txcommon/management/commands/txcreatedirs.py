import os
from django.core.management.base import NoArgsCommand

def transifex_paths():
    from django.conf import settings as s
    # Scratch dir
    yield s.SCRATCH_DIR
    # Msgmerge dir
    yield s.MSGMERGE_DIR
    # Repo paths
    for vcs in s.CODEBASE_CHOICES.keys():
        yield s.REPO_PATHS[vcs]
    # Log path
    yield s.LOG_PATH


class Command(NoArgsCommand):
    help = 'Create scratchdir vcs directories'

    requires_model_validation = False
    can_import_settings = True

    def handle_noargs(self, **options):
        for path in transifex_paths():
            try:
                os.makedirs(path)
                print "Creating %s" % path
            except OSError, e:
                print "Error creating %s: %s" % (path, e.strerror)

