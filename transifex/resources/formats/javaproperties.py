# -*- coding: utf-8 -*-

"""
Java properties file handler/compiler
"""
import os, re
import codecs
from django.utils.hashcompat import md5_constructor

from transifex.txcommon.log import logger
from transifex.resources.models import SourceEntity
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import GenericTranslation, Handler, \
        STRICT, StringSet

class JavaPropertiesHandler(Handler):
    """
    Handler for Java PROPERTIES translation files.
    """

    name = "Java *.PROPERTIES file handler"
    mime_types = []
    format = "Java PROPERTIES (*.properties)"

    separators = [' ', '\t', '\f', '=', ':', ]

    @classmethod
    def accepts(cls, filename=None, mime=None):
        return filename.endswith(".properties") or mime in cls.mime_types

    @classmethod
    def contents_check(self, filename):
        pass

    def __str__(self):
        s='{'
        for key,value in self._props.items():
            s = ''.join((s,key,'=',value,', '))

        s=''.join((s[:-2],'}'))
        return s

    def _split(self, line):
        """
        Split a line in (key, value).

        The separator is the first non-escaped charcter of (\s,=,:).
        If no such character exists, the wholi line is a key with no value.
        """
        for i, c in enumerate(line):
            if c in self.separators and not self._is_escaped(line, i):
                # Seperator found
                key = line[:i].lstrip()
                value = self._strip_separators(line[i+1:])
                return (key, value)
        return (line, None)

    def _strip_separators(self, s):
        """Strip separators from the front of the string s."""
        return s.lstrip(''.join(self.separators))

    def _is_escaped(self, line, index):
        """
        Returns True, if the character of index is escaped by backslashes.

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

    def _parse(self, fh):
        """
        Parse a file handle and create an internal property dictionary.

        See http://download.oracle.com/javase/1.4.2/docs/api/java/util/PropertyResourceBundle.html,
        http://download.oracle.com/javase/1.4.2/docs/api/java/util/Properties.html#encoding and
        http://download.oracle.com/javase/1.4.2/docs/api/java/util/Properties.html#load(java.io.InputStream)
        for details.

        Args:
            fh: an open file handle.

        Returns:
            the original file as a buffer.
        """

        # Every line in the file must consist of either a comment
        # or a key-value pair. A key-value pair is a line consisting
        # of a key which is a combination of non-white space characters
        # The separator character between key-value pairs is a '=',
        # ':' or a whitespace character not including the newline.
        # If the '=' or ':' characters are found, in the line, even
        # keys containing whitespace chars are allowed.

        # A line with only a key according to the rules above is also
        # fine. In such case, the value is considered as the empty string.
        # In order to include characters '=' or ':' in a key or value,
        # they have to be properly escaped using the backslash character.

        # Some examples of valid key-value pairs:
        #
        # key     value
        # key=value
        # key:value
        # key     value1,value2,value3
        # key     value1,value2,value3 \
        #         value4, value5
        # key
        # This key= this value
        # key = value1 value2 value3

        # Any line that starts with a '#' or '!' is considerered a comment
        # and skipped. Also any trailing or preceding whitespaces
        # are removed from the key/value.

        # This is a line parser. It parses the contents line by line.

        buf = u""
        for line in fh:
            buf += line
            line = self._prepare_line(line)
            # Skip empty lines and comments
            if not line or line.startswith(('#','!', )):
                continue
            # If the last character is a backslash
            # it has to be preceded by a space in which
            # case the next line is read as part of the
            # same property
            while line[-1] == '\\' and not self._is_escaped(line, -1):
                # Read next line
                nextline = self._prepare_line(fh.next())
                # This line will become part of the value
                line = line[:-1] + nextline
            key, value = self._split(line)
            if value is None:
                continue
            self.processPair(self.unescape(key), self.unescape(value))
        return buf

    def _prepare_line(self, line):
        """Prepare a line for parsing."""
        return line.strip('\r\n').strip()

    def processPair(self, key, value):
        """ Process a (key, value) pair """
        logger.debug("%s=%s\n" % (key, value))
        self._props[key] = value.strip()

    def escape(self, value):
        """
        Escape special characters in Java properties files.

        Java escapes the '=' and ':' in the value
        string with backslashes in the store method.
        So let us do the same.
        """
        return (value.replace(':','\:')
                     .replace('=','\=')
                     .replace(' ','\ ')
                     .replace('\\', '\\\\')
        )

    def unescape(self, value):
        """Reverse the escape of special characters."""
        return (value.replace('\:',':')
                     .replace('\=','=')
                     .replace('\ ', ' ')
                     .replace('\\\\', '\\')
        )

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parse a java .properties file and create a stringset with all entries in the file.
        """
        resource = self.resource
        stringset = StringSet()
        suggestions = StringSet()
        self._props = {}

        try:
            fh = codecs.open(self.filename, "r", encoding="UTF-8")
            buf = self._parse(fh)
        finally:
            fh.close()
        for source, trans in self._props.iteritems():
            line = (source + '=' + trans)#.decode('utf-8')
            # We use empty context
            context = ""

            if is_source:
                if trans.strip()!="":
                    new_line = re.sub(
                        re.escape(trans),
                        "%(hash)s_tr" % {'hash': hash_tag(source,context)},
                        line
                    )

                    # this looks fishy
                    buf = re.sub(re.escape(line), new_line, buf)
                else:
                    continue
            else:
                try:
                    if SourceEntity.objects.get(resource=resource, string=source):
                        pass
                    else:
                        continue
                except:
                    continue

            stringset.strings.append(GenericTranslation(source,
                trans, rule=5, context=context,
                pluralized=False, fuzzy=False,
                obsolete=False))

        self.stringset=stringset
        self.suggestions=suggestions

        if is_source:
            self.template = str(buf.encode('utf-8'))

    def _do_replace(self, original, replacement, text):
        return re.sub(re.escape(original), self.escape(replacement), text)
