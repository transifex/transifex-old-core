from translations.lib.types.pot import POTManager
from transifex.log import logger

class POTHandler():
    """
    POTManager abstraction layer, specific to the projects app.
    
    You can use this higher-level object to interact with a
    component's statistics instead of meddling with the lower-
    level POTManager. Each Component obect gets one of these
    as ``component.trans``.
    
    """

    def __init__(self, component):
        self.component = component
        self.tm = POTManager(component.get_files(),
                             component.unit.browser.path, 
                             component.source_lang)

    def get_manager(self):
        return self.tm

    def set_stats_for_lang(self, lang):
        """Set stats for a specific language."""
        return self.tm.create_stats(lang, self.component)

    def set_stats(self):
        """Calculate stats for all translations of the component."""

        # Deleting all stats for the component
        logger.debug("Setting stats for %s" % self.component)
        self.tm.delete_stats_for_object(self.component)

        for lang in self.tm.get_langs():
            self.set_stats_for_lang(lang)
        
    def get_stats(self):
        """Return stats for the component."""
        return self.tm.get_stats(self.component)

    def get_file_content(self, filename):
        """Return stats for the component."""
        return self.tm.get_file_content(filename)

    def get_source_file(self):
        return self.tm.get_source_file()
