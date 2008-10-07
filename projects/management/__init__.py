from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _

if settings.ENABLE_NOTICES:
    try:
        # TODO: Document why we do it here instead of a fixture?
        from notification import models as notification
        
        def create_notice_types(app, created_models, verbosity, **kwargs):
            notification.create_notice_type("projects_added_new",
                                           _("New Project Added"), 
                                           _("when a new project is added"), 
                                           default=1)
            notification.create_notice_type("projects_added_new_component", 
                                           _("New Component Added"), 
                                           _("when a new component is added"), 
                                           default=1)
        signals.post_syncdb.connect(create_notice_types, sender=notification)
    except ImportError:
        print "Skipping creation of NoticeTypes as notification app not found"
     
