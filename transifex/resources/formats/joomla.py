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
    format = "Joomla INI (*.ini)"
    method_name = 'INI'
    comment_chars = ('#', ';', ) # '#' is for 1.5 and ';' for >1.6

    def is_content_valid(self, filename):
        pass

    def __init__(self, filename=None, resource= None, language = None):
        super(JoomlaINIHandler, self).__init__(filename, resource, language)

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

        jformat = JoomlaIniVersion.create(buf)

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

            trans = jformat.get_translation(trans)

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


class JoomlaIniVersion(object):
    """Base class for the various formats of Joomla ini files."""

    @classmethod
    def create(cls, content):
        """Factory method to return the correct instance for the format.

        In versions >=1.6 translations are surrounded by double quotes.
        """
        if content[0] == ';':
            return JoomlaIniNew()
        else:
            return JoomlaIniOld()

    def get_translation(self, value):
        """
        Return the trasnlation value extracted from the specified string.
        """
        raise NotImplementedError


class JoomlaIniOld(JoomlaIniVersion):
    """Format for Joomla 1.5."""

    def get_translation(self, value):
        return value


class JoomlaIniNew(JoomlaIniVersion):
    """Format for Joomla 1.6."""

    def get_translation(self, value):
        # Get rid of double-quote at the start and end of value
        return value[1:-1]
