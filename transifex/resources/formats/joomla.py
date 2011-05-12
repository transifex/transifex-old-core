# -*- coding: utf-8 -*-

"""
Joomla INI file handler/compiler
"""
import os, re
import codecs

from transifex.txcommon.log import logger
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import GenericTranslation, Handler, \
        STRICT, StringSet

class JoomlaINIHandler(Handler):
    """
    Handler for Joomla's INI translation files.

    See http://docs.joomla.org/Specification_of_language_files
    and http://docs.joomla.org/Creating_a_language_definition_file.
    """
    name = "Joomla *.INI file handler"
    mime_types = []
    format = "Joomla INI (*.ini)"
    comment_chars = ('#', ';', ) # '#' is for 1.5 and ';' for >1.6

    @classmethod
    def accepts(cls, filename=None, mime=None):
        accept = False
        if filename is not None:
            accept |= filename.endswith(".ini")
        if mime is not None:
            accept |= mime in cls.mime_types
        return accept

    @classmethod
    def contents_check(self, filename):
        pass

    def __init__(self, filename=None, resource= None, language = None):
        super(JoomlaINIHandler, self).__init__(filename, resource, language)
        self._version = 0

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
            if not line or line.startswith(self.comment_chars):
                continue

            try:
                source, trans = line.split('=', 1)
            except ValueError:
                # Maybe abort instead of skipping?
                logger.error('Could not parse line "%s". Skipping...' % line)
                continue

            # In versions >=1.6 translations are surrounded by double quotes. So remove them
            # Normally, if the translation starts with '"', it is a 1.6-file and must
            # end with '"', since translations starting with '"' are not allowed in 1.5.
            # But, let's check both the first and last character of the translation to be safe.
            if trans.startswith('"') and trans.endswith('"'):
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

    def _peek_into_template(self):
        """
        If the first line begins with ';', mark the version of the
        ini file as 1 (>=1.6), else as 0 (==1.5).
        """
        if self.template.startswith(';'):
            self._version = 1
        else:
            self._version = 0

    def _do_replace(self, original, replacement, text):
        """
        Replace `original` with `replacement` in `text`.

        Joomla versions >=1.6 need the replacement to be enclosed in double quotes
        first.
        """
        if self._version:
            replacement = ''.join(['"', replacement, '"'])
        return super(JoomlaINIHandler, self)._do_replace(original, replacement, text)
