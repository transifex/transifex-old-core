# -*- coding: utf-8 -*-

"""
Joomla INI file handler/compiler
"""
import os, re
import codecs
from django.utils.hashcompat import md5_constructor

from transifex.txcommon.log import logger
from transifex.resources.formats.decorators import *

from core import GenericTranslation, Handler, STRICT, \
    StringSet

class INIHandler(Handler):
    """
    Handler for Joomla's INI translation files.
    """
    name = "Joomla *.INI file handler"
    mime_types = []
    format = "Joomla INI (*.ini)"

    @classmethod
    def accept(cls, filename=None, mime=None):
        return filename.endswith(".ini") or mime in cls.mime_types

    @classmethod
    def contents_check(self, filename):
        pass

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parse an INI file and create a stringset with all entries in the file.
        """
        stringset = StringSet()
        suggestions = StringSet()

        fh = codecs.open(self.filename, "r", "utf-8")

        buf = fh.read()
        fh.close()

        for line in buf.split('\n'):
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            try:
                source, trans = line.split('=', 1)
            except ValueError:
                # Maybe abort instead of skipping?
                logger.error('Could not parse line "%s". Skipping...' % line)
                continue

            # We use empty context
            context = ""

            if is_source:
                new_line = re.sub(re.escape(trans), "%(hash)s_tr" % {'hash':md5_constructor(
                    ':'.join([source,context]).encode('utf-8')).hexdigest()}, line)

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
