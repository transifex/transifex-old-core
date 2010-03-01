from django.conf import settings
from projects.handlers.types import pot
from txcommon.log import logger
from notification import models as notification

class IntltoolHandler(pot.POTHandler):
    """
    POTHandler abstraction layer, hense specific to the projects app.
    
    You can use this higher-level object to interact with a
    component's statistics that use intltool instead of meddling with 
    the lower-level POTManager. Each Component object gets one of these
    as ``component.trans``.
    
    """

    def set_stats(self):
        """
        Calculate stats for all translations of the component after 
        these translations are merged with a new POT file extracted 
        using intltool-update.    .
        """

        logger.debug("Setting stats for %s" % self.component)

        isIntltooled = self.tm.intltool_update()
        if not isIntltooled:
            logger.debug("intltool-update --pot has failed for %s" % 
                         self.component)

            if settings.ENABLE_NOTICES:
                notification.send(self.component.project.maintainers.all(),
                                  'project_component_potfile_error',
                                  {'component': self.component})
            is_msgmerged=False
        else:
            is_msgmerged=True

        self.set_source_stats(is_msgmerged=False)
        self.set_po_stats(is_msgmerged)
        # Cleaning the repository after running intltool-update
        self.component.unit.browser._clean_dir()
        self.clean_old_stats()
