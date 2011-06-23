# -*- coding: utf-8 -*-

"""
Java properties file handler/compiler
"""
import os, re
from django.utils.hashcompat import md5_constructor

from transifex.txcommon.log import logger
from transifex.resources.models import SourceEntity
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import GenericTranslation, Handler, \
        STRICT, StringSet, ParseError


class JavaParseError(ParseError):
    pass


class JavaCompileError(CompileError):
    pass


class JavaPropertiesHandler(Handler):
    """
    Handler for Java PROPERTIES translation files.

    Java properties files *must* be encoded in cls.default_encoding encoding.
    """

    name = "Java *.PROPERTIES file handler"
    format = "Java PROPERTIES (*.properties)"
    method_name = 'PROPERTIES'
    format_encoding = 'ISO-8859-1'

    SEPARATORS = [' ', '\t', '\f', '=', ':', ]
    COMMENT_CHARS = ('#', '!', )

    def _escape(self, s):
        """
        Escape special characters in Java properties files.

        Java escapes the '=' and ':' in the value
        string with backslashes in the store method.
        So let us do the same.
        """
        return (s.replace(':', '\:')
                .replace('=', '\=')
                .replace('\\', '\\\\')
        )

    def _find_linesep(self, s):
        """Find the line separator used in the file."""
        if "\r\n" in s:         # windows line ending
            self._linesep = "\r\n"
        elif "\r" in s:         # macosx line ending
            self._linesep = "\r"
        else:
            self._linesep = "\n"

    def _is_escaped(self, line, index):
        """
        Returns True, if the character at index is escaped by backslashes.

        There has to be an even number of backslashes before the character for
        it to be escaped.
        """
        nbackslashes = 0
        for c in reversed(line[:index]):
            if c == '\\':
                nbackslashes += 1
            else:
                break
        return nbackslashes % 2 == 1

    def _iter_by_line(self):
        """Iterate the content by line."""
        for line in self.content.split(self._linesep):
            yield line

    def _prepare_line(self, line):
        """
        Prepare a line for parsing.

        Remove newline and whitespace characters.
        """
        return line.strip('\r\n').strip()

    def _split(self, line):
        """
        Split a line in (key, value).

        The separator is the first non-escaped charcter of (\s,=,:).
        If no such character exists, the wholi line is a key with no value.
        """
        for i, c in enumerate(line):
            if c in self.SEPARATORS and not self._is_escaped(line, i):
                # Seperator found
                key = line[:i].lstrip()
                value = self._strip_separators(line[i+1:])
                return (key, value)
        return (line, None)

    def _strip_separators(self, s):
        """Strip separators from the front of the string s."""
        return s.lstrip(''.join(self.SEPARATORS))

    def _unescape(self, value):
        """Reverse the escape of special characters."""
        return (value.replace('\:', ':')
                     .replace('\=', '=')
                     .replace('\ ', ' ')
                     .replace('\\\\', '\\')

    def convert_to_unicode(self, s):
        """Convert the string s to a proper unicode string.

        Java .properties files go through native2ascii first, which
        converts unicode characters to \uxxxx representations, ie to a series
        of bytes that represent the original unicode codepoint.

        We convert each \uxxxx representation back to the unicode character
        by finding the decimal representation of it and then
        calling ord on the result.

        Args:
            s: A string of the form '\\uxxxx'.
        Returns:
            The unicode character that corresponds to that.
        """
        assert len(s) == 6
        char = 0
        base = 16
        for rank, c in enumerate(reversed(s[2:])):
            char += int(c, base) * base ** rank
        return unichr(char)

    def convert_to_ascii(self, c):
        """Convert the character c to a \uxxxx representation.

        THe method converts a unicode character c to a series of bytes
        that represent its codepoint.

        Args:
            c: The unicode character to convert.
        Returns:
            A string that represents its codepoint.
        """
        assert len(c) == 1
        s = ''
        base = 16
        n = ord(c)
        for i in xrange(4):
            (n, mod) = divmod(n, base)
            s = ''.join([hex(mod)[2], s])
        return ''.join(['\\u', s])


    def _replace_translation(self, original, replacement, text):
        """Convert unicode characters to sequence of bytes representing the
        codepoints.
        """
        replacement = replacement.decode('UTF-8')
        for char in replacement:
            if ord(char) > 127:
                replacement = replacement.replace(char, self.convert_to_ascii(char))
        replacement = replacement.encode('UTF-8')
        return super(JavaPropertiesHandler, self)._replace_translation(
            original, replacement, text
        )

    def _parse(self, is_source, lang_rules):
        """
        Parse a java .properties content and create a stringset with
        all entries in it.

        See
        http://download.oracle.com/javase/1.4.2/docs/api/java/util/PropertyResourceBundle.html,
        http://download.oracle.com/javase/1.4.2/docs/api/java/util/Properties.html#encoding and
        http://download.oracle.com/javase/1.4.2/docs/api/java/util/Properties.html#load(java.io.InputStream)
        for details.
        """
        resource = self.resource

        context = ""
        self._find_linesep(self.content)
        buf = u""
        lines = self._iter_by_line()
        for line in lines:
            line = self._prepare_line(line)
            # Skip empty lines and comments
            if not line or line.startswith(self.COMMENT_CHARS):
                if is_source:
                    buf += line + self._linesep
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

            if value is not None:
                uni_chars = re.findall(r'(\\u[0-9A-Fa-f]{4})', value)
                for uni_char in uni_chars:
                    value = value.replace(
                        uni_char, self.convert_to_unicode(uni_char)
                    )

            if is_source:
                if not value:
                    buf += line + self._linesep
                    # Keys with no values should not be shown to translator
                    continue
                else:
                    buf += re.sub(
                        re.escape(value),
                        "%(hash)s_tr" % {'hash': hash_tag(key, context)},
                        line
                    ) + self._linesep
            elif not SourceEntity.objects.filter(resource=resource, string=key).exists():
                # ignore keys with no translation
                continue

            self.stringset.strings.append(GenericTranslation(key,
                self._unescape(value), rule=5, context=context,
                pluralized=False, fuzzy=False,
                obsolete=False))
        return buf
