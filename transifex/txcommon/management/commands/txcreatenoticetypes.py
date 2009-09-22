import os
from django.core.management.base import NoArgsCommand
from notification import models as notification
from txcommon.notifications import NOTICE_TYPES

def create_notice_types():
    for n in NOTICE_TYPES:
            notification.create_notice_type(n["label"], n["display"], 
                                            n["description"], n["default"])

class Command(NoArgsCommand):
    help = ('Create or Update the notice types used in the ActionLog and '
           'Notification apps')

    requires_model_validation = False
    can_import_settings = False

    def handle_noargs(self, **options):
        print "Creating or updating notice types"
        create_notice_types()
        print "Default set of notice types initialized successfully."
