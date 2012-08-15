# -*- coding: utf-8 -*-

"""
Magento CSV handler
"""
import os, re
import codecs

from transifex.txcommon.log import logger
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import GenericTranslation, Handler, \
        STRICT, StringSet

class MagentoCSVHandler(Handler):
    """
    Handler for Magento CSV files.
    """
    name = "Magento *.csv handler"
    format = "Magento CSV (*.csv)"
    comment_chars = ('#', ';', )

    @classmethod
    def accepts(cls, filename=None, mime=None):
        accept = False
        if filename is not None:
            accept |= filename.endswith(".csv")
        if mime is not None:
            accept |= mime in cls.mime_types
        return accept

    @classmethod
    def contents_check(self, filename):
        pass

    def __init__(self, filename=None, resource= None, language = None):
        super(MagentoCSVHandler, self).__init__(filename, resource, language)

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parse an CSV file and create a stringset with all entries in the file.
        """
        stringset = StringSet()
        suggestions = StringSet()

        fh = codecs.open(self.filename, "r", "utf-8")
        try:
            buf = fh.read()
        finally:
            fh.close()

        for line in buf.split('\n'):

            # Skip empty lines and comments
            if not line or line.startswith(self.comment_chars):
                continue

            try:
                source, trans = line.split(',', 1)
            except ValueError:
                logger.error('Could not parse line "%s"' % line)
                continue

            # CSV-strings are surrounded by quotes, which need to be removed
            if source.startswith('"') and source.endswith('"'):
                source = source[1:-1]

            if source.startswith('\'') and source.endswith('\''):
                source = source[1:-1]

            if trans.startswith('"') and trans.endswith('"'):
                trans = trans[1:-1]

            if trans.startswith('\'') and trans.endswith('\''):
                trans = trans[1:-1]

            # We use empty context
            context = ""

            if is_source:
                new_line = re.sub(
                    re.escape(trans),
                    "%(hash)s_tr" % {'hash': hash_tag(source, context)},
                    line
                )
                # this looks fishy
                buf = re.sub(re.escape(line), new_line, buf)

            stringset.strings.append(GenericTranslation(source,
                trans, rule=5, context=context,
                pluralized=False, fuzzy=False,
                obsolete=False))

        self.stringset=stringset
        self.suggestions=suggestions

        if is_source:
            self.template = str(buf.encode('utf-8'))

