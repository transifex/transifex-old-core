from django.conf import settings
from django.db.models import signals
from notification import models as notification
from txcommon import models as txcommon_app
from txcommon.notifications import NOTICE_TYPES

def create_notice_types(app, created_models, verbosity, **kwargs):
    for n in NOTICE_TYPES:
            notification.create_notice_type(n["label"],
                                            n["display"], 
                                            n["description"], 
                                            n["default"])

signals.post_syncdb.connect(create_notice_types, sender=txcommon_app)
