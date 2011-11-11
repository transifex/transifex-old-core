# -*- coding: utf-8 -*-

"""
Mozilla properties file handler/compiler
"""
import os, re
from django.utils.hashcompat import md5_constructor

from transifex.txcommon.log import logger
from transifex.resources.models import SourceEntity
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import Handler, ParseError, CompileError
from transifex.resources.formats.resource_collections import StringSet, \
        GenericTranslation
from transifex.resources.formats.javaproperties import JavaPropertiesHandler

class MozillaPropertiesHandler(JavaPropertiesHandler):
    name = "Mozilla *.PROPERTIES file handler"
    format = "Mozilla PROPERTIES (*.properties)"
    method_name = 'MOZILLAPROPERTIES'
    format_encoding = 'UTF-8'


    def _escape(self, s):
        """
        Escape special characters in Mozilla properties files.

        Java escapes the '=' and ':' in the value
        string with backslashes in the store method.
        Mozilla escapes only '\\'.
        """
        return s.replace('\\', '\\\\')

    def _unescape(self, value):
        """Reverse the escape of special characters."""
        return value.replace('\\\\', '\\')

    def _replace_translation(self, original, replacement, text):
        return text.replace(
            original, self._pseudo_decorate(self._escape(replacement))
        )

    def _parse(self, is_source, lang_rules):
        """
        Parse a mozilla .properties content and create a stringset with
        all entries in it.

        See http://www-archive.mozilla.org/projects/l10n/mlp_what2.html
        for details.
        """
        resource = self.resource

        context = ""
        self._find_linesep(self.content)
        template = u""
        lines = self._iter_by_line(self.content)
        for line in lines:
            line = self._prepare_line(line)
            # Skip empty lines and comments
            if not line or line.startswith(self.comment_chars):
                if is_source:
                    template += line + self.linesep
                continue
            # If the last character is a backslash
            # it has to be preceded by a space in which
            # case the next line is read as part of the
            # same property
            while line[-1] == '\\' and not self._is_escaped(line, -1):
                # Read next line
                nextline = self._prepare_line(lines.next())
                # This line will become part of the value
                line = line[:-1] + self._prepare_line(nextline)
            key, value = self._split(line)

            if is_source:
                if not value:
                    template += line + self.linesep
                    # Keys with no values should not be shown to translator
                    continue
                else:
                    key_len = len(key)
                    template += line[:key_len] + re.sub(
                        re.escape(value),
                        "%(hash)s_tr" % {'hash': hash_tag(key, context)},
                        line[key_len:]
                    ) + self.linesep
            elif not SourceEntity.objects.filter(resource=resource, string=key).exists():
                # ignore keys with no translation
                continue
            self._add_translation_string(
                key, self._unescape(value), context=context
            )
        return template
