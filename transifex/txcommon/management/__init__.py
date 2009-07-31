from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
from txcommon import models as txcommon_app

# This is temporary
NOTICE_TYPES = [
            {
                "label": "project_added",
                "display": _("New Project Added"), 
                "description": _("when a new project is added"), 
                "default": 1,
                "show_to_user": False,
            },
            {
                "label": "project_changed",
                "display": _("Project Changed"), 
                "description": _("when a project is changed"), 
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_deleted",
                "display": _("Project Deleted"), 
                "description": _("when a project is deleted"), 
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_component_added",
                "display": _("New Component Added"), 
                "description": _("when a new component is added to a project"), 
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_component_changed",
                "display": _("Component Changed"), 
                "description": _("when a component of a project is changed"), 
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_component_deleted",
                "display": _("Component Deleted"), 
                "description": _("when a component of a project is deleted"), 
                "default": 1,
                "show_to_user": True,
            },
            {
                "label": "project_component_file_submitted",
                "display": _("File Submitted"), 
                "description": _("when a component file of a project"
                                 " is submitted"), 
                "default": 2,
                "show_to_user": False,
            },
            {
                "label": "project_component_file_changed",
                "display": _("Translation File Changed"),
                "description": _("when a component translation file of a"
                                 " project is changed"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_component_potfile_error",
                "display": _("Translation Source File (POT) has a Problem"),
                "description": _("when the source file (POT) of a"
                                 " component that you are a maintainer"
                                 " has a problem"), 
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "collection_added",
                "display": _("New Collection Added"), 
                "description": _("when a new collection is added"), 
                "default": 1,
                "show_to_user": False,
            },
            {
                "label": "collection_changed",
                "display": _("Collection Changed"), 
                "description": _("when a collection is changed"), 
                "default": 1,
                "show_to_user": False,
            },
            {
                "label": "collection_deleted",
                "display": _("Collection Deleted"), 
                "description": _("when a collection is deleted"), 
                "default": 1,
                "show_to_user": False,
            },
            {
                "label": "collection_project_added",
                "display": _("Project Added to a Collection"), 
                "description": _("when a new project is added to a collection"), 
                "default": 2,
                "show_to_user": False,
            },
            {
                "label": "collection_project_deleted",
                "display": _("Project Deleted from a Collection"), 
                "description": _("when a project is deleted from a collection"), 
                "default": 2,
                "show_to_user": False,
            }, 
            {
                "label": "collection_release_added",
                "display": _("New Release Added for a Watched Collection"), 
                "description": _("when a new release is added to"
                                " a collection"), 
                "default": 2,
                "show_to_user": False,
            },
            {
                "label": "collection_release_changed",
                "display": _("Release Changed"), 
                "description" :_("when a release of a collection is changed"), 
                "default": 1,
                "show_to_user": False,
            },
            {   "label": "collection_release_deleted",
                "display": _("Release Deleted"), 
                "description": _("when a release of a collection is deleted"), 
                "default": 1,
                "show_to_user": False,
            },
            {   "label": "collection_release_component_added",
                "display": _("Release Added to a Collection"), 
                "description": _("when a release is added to a collection"), 
                "default": 2,
                "show_to_user": False,
            },
            {   "label": "collection_release_component_deleted",
                "display": _("Release Deleted from a Collection"), 
                "description": _("when a release is deleted from a collection"), 
                "default": 2,
                "show_to_user": False,
            },
    ]

try:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        for n in NOTICE_TYPES:
                notification.create_notice_type(n["label"],
                                                n["display"], 
                                                n["description"], 
                                                n["default"])

    signals.post_syncdb.connect(create_notice_types, sender=txcommon_app)
except ImportError:
    print "Skipping creation of NoticeTypes as notification app not found"
