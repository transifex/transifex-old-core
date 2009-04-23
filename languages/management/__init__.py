
from django.db.models import signals
from languages import models as lang_app

def create_languages(app, created_models, verbosity, **kwargs):
    from languages.models import Language
    from django.core.management import call_command
    if Language in created_models and kwargs.get('interactive', True):
        msg = ("\nTransifex's language tables were just initialized.\n"
               "Would you like to populate them now with a standard set of "
               "languages? (yes/no): ")
        confirm = raw_input(msg)
        while 1:
            if confirm not in ('yes', 'no'):
                confirm = raw_input('Please enter either "yes" or "no": ')
                continue
            if confirm == 'yes':
                call_command("create_languages", interactive=True)
            break

signals.post_syncdb.connect(create_languages,
    sender=lang_app, dispatch_uid = "languages.management.create_languages")
