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


class JavaPropertiesHandler(Handler):
    """
    Handler for Java PROPERTIES translation files.

    Java properties files *must* be encoded in cls.ENCODING encoding.
    """

    name = "Java *.PROPERTIES file handler"
    mime_types = []
    format = "Java PROPERTIES (*.properties)"

    SEPARATORS = [' ', '\t', '\f', '=', ':', ]
    COMMENT_CHARS = ('#', '!', )
    ENCODING = 'ISO-8859-1'

    def _do_replace(self, original, replacement, text):
        """Substitute hash code with escaped value of translation."""
        return re.sub(re.escape(original), self.escape(replacement), text)

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

    def _post_save2file(self, *args, **kwargs):
        self.compiled_template = self.compiled_template.decode(self.ENCODING)

    def _pre_save2file(self, *args, **kwargs):
        self.compiled_template = self.compiled_template.encode(self.ENCODING)

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

    @classmethod
    def accepts(cls, filename=None, mime=None):
        return filename.endswith(".properties") or mime in cls.mime_types

    @classmethod
    def contents_check(self, filename):
        pass

    def escape(self, value):
        """
        Escape special characters in Java properties files.

        Java escapes the '=' and ':' in the value
        string with backslashes in the store method.
        So let us do the same.
        """
        return (value.replace(':', '\:')
                     .replace('=', '\=')
                     .replace(' ', '\ ')
                     .replace('\\', '\\\\')
        )

    def find_linesep(self, file_):
        """Find the line separator used in the file."""
        line = file_.readline()
        if line.endswith("\r\n"):  # windows line ending
            self._linesep = "\r\n"
        elif line.endswith("\r"):  # macosx line ending
            self._linesep = "\r"
        else:
            self._linesep = "\n"
        file_.seek(0)

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parse a java .properties file and create a stringset with
        all entries in the file.

        See
        http://download.oracle.com/javase/1.4.2/docs/api/java/util/PropertyResourceBundle.html,
        http://download.oracle.com/javase/1.4.2/docs/api/java/util/Properties.html#encoding and
        http://download.oracle.com/javase/1.4.2/docs/api/java/util/Properties.html#load(java.io.InputStream)
        for details.
        """
        resource = self.resource
        stringset = StringSet()
        suggestions = StringSet()

        context = ""
        fh = open(self.filename, "r")
        try:
            self.find_linesep(fh)
            buf = u""
            for line in fh:
                line = line.decode(self.ENCODING)
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
                    nextline = self._prepare_line(fh.next())
                    # This line will become part of the value
                    line = line[:-1] + self._prepare_line(nextline)
                key, value = self._split(line)

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

                stringset.strings.append(GenericTranslation(key,
                    self.unescape(value), rule=5, context=context,
                    pluralized=False, fuzzy=False,
                    obsolete=False))
        except UnicodeDecodeError, e:
            # raise JavaParseError(
            #     'Java .proeprties files must be in %s encoding.' % self.ENCODING
            # )
            raise JavaParseError(e.message)
        finally:
            fh.close()

        self.stringset=stringset
        self.suggestions=suggestions

        if is_source:
            self.template = str(buf.encode('utf-8'))

    def unescape(self, value):
        """Reverse the escape of special characters."""
        return (value.replace('\:', ':')
                     .replace('\=', '=')
                     .replace('\ ', ' ')
                     .replace('\\\\', '\\')
        )
