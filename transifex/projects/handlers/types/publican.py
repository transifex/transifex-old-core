from projects.handlers.types import pot
from translations.lib.types.publican import PublicanManager
from txcommon.log import logger

class PublicanHandler(pot.POTHandler):
    """
    A POTHandler abstraction for Publican projects.

    https://fedorahosted.org/publican

    Use this higher-level object to interact with a component's statistics 
    instead of meddling with the lower-level POTManager. 

    Each Component object gets one of these as ``component.trans``.

    """
    def __init__(self, component):
        self.component = component
        # TODO: Make Unit init the browser on its own 
        component.unit._init_browser()
        browser = component.unit.browser
        self.tm = PublicanManager(component.full_name, browser.path, 
            component.source_lang, component.file_filter)

    def set_stats(self):
        """Calculate stats for all translations of the component."""

        logger.debug("Setting stats for %s" % self.component)

        # Copying the source file to the static dir
        try:
            logger.debug("Copying source files of %s to static dir" % self.component)
            potfiles = self.tm.get_source_files()
            for potfile in potfiles:
                self.tm.copy_file_to_static_dir(potfile)
        except (AttributeError, IOError):
            logger.debug("Error copying source files. There is no source file (POT)")
            pass

        self.set_source_stats(is_msgmerged=False)
        self.set_po_stats(is_msgmerged=False)
        self.clean_old_stats()
