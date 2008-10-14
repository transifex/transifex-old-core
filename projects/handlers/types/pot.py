from translations.lib.types.pot import POTManager

class POTHandler():

    def __init__(self, component):
        
        self.component = component
        self.tm = POTManager(component.get_files(),
                             component.unit.browser.path, 
                             component.source_lang)

    def set_stats_for_lang(self, lang):
        """Set stats for a determinated language."""
        return self.tm.create_stats(lang, self.component)

    def set_stats(self):
        """
        This method is responsable to set up the statistics for a 
        component, calculing the stats for each translation present on it.
        """
        # Initializing the component's unit
        self.component.unit.init_browser()
        # Unit checkout
        self.component.unit.browser.update()
        # Deleting all stats for the component
        self.tm.delete_stats_for_object(self.component)

        for lang in self.tm.get_langs():
            self.set_stats_for_lang(lang)
        
    def get_stats(self):
        return self.tm.get_stats(self.component)

    def get_file_content(self, filename):
        return self.tm.get_file_content(filename)
