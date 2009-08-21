import os
import polib
from translations.lib.types.pot import POTManager
from translations.models import POFile
from txcommon.log import logger

class POTHandler:
    """
    POTManager abstraction layer, specific to the projects app.
    
    You can use this higher-level object to interact with a
    component's statistics instead of meddling with the lower-
    level POTManager. Each Component object gets one of these
    as ``component.trans``.
    
    """

    def __init__(self, component):
        self.component = component
        # TODO: Make Unit init the browser on its own 
        component.unit._init_browser()
        browser = component.unit.browser
        if hasattr(browser, 'filepath'):
            filepath = browser.filepath
        else:
            filepath = None
        self.tm = POTManager(component.get_files(),
                             browser.path, 
                             component.source_lang,
                             component.file_filter,
                             filepath)

    def get_manager(self):
        return self.tm

    def set_stats_for_lang(self, lang, try_to_merge=True):
        """Set stats for a specific language."""
        return self.tm.create_lang_stats(lang, self.component, try_to_merge)

    def set_stats(self):
        """Calculate stats for all translations of the component."""

        logger.debug("Setting stats for %s" % self.component)

        # Copying the source file to the static dir
        try:
            potfiles = self.tm.get_source_files()
            for potfile in potfiles:
                self.tm.copy_file_to_static_dir(potfile)
        except (AttributeError, IOError):
            # TODO: There is no source file (POT)
            # It looks like an intltool POT-based, what should we do?
            pass

        # Set the source file (pot) to the database
        self.tm.set_source_stats(self.component, is_msgmerged=False)

        for lang in self.tm.get_langs():
            self.set_stats_for_lang(lang)

        self.clear_old_stats()

    def clear_old_stats(self):
        """
        Clear stats present on the database and msgmerge dir, that are not 
        anymore in the upstream repository
        """
        pofiles = POFile.objects.select_related().filter(
            component=self.component)
        pots = self.tm.get_source_files()
        files = self.tm.get_po_files()
        for pot in pots:
            files.append(pot)
        for stat in pofiles:
            if stat.filename not in files:
                self.tm.delete_file_from_static_dir(stat.filename)
                stat.delete()

    def clear_stats(self):
        """Clear stats for all translations of the component."""

        # Deleting all stats for the component
        logger.debug("Clearing stats for %s" % self.component)
        self.tm.delete_stats_for_object(self.component)

    def get_stats(self):
        """Return stats for the component."""
        return self.tm.get_stats(self.component)

    def get_file_content(self, filename, is_msgmerged):
        """Return stats for the component."""
        return self.tm.get_file_content(filename, is_msgmerged)

    def get_po_entries(self, filename):
        """Return a Django form field for the component"""
        return self.tm.get_po_entries(filename)

    def get_source_stats(self):
        return self.tm.get_source_stats(self.component)

    def get_source_file(self):
        return self.tm.get_source_file()

    def guess_language(self, filename):
        """Set stats for a specific language."""
        return self.tm.guess_language(filename)

    def msgfmt_check(self, po_contents):
        """Check a POT/PO file with msgfmt -c."""
        return self.tm.msgfmt_check(po_contents)
