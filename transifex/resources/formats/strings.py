# -*- coding: utf-8 -*-

"""
Apple strings file handler/compiler
"""
import os, re, chardet

from transifex.txcommon.log import logger
from transifex.resources.models import SourceEntity, Template
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import GenericTranslation, Handler, \
        STRICT, StringSet, ParseError


class StringsParseError(ParseError):
    pass


class AppleStringsHandler(Handler):
    """
    Handler for Apple STRINGS translation files.

    Apple strings files *must* be encoded in cls.ENCODING encoding.
    """

    name = "Apple *.STRINGS file handler"
    mime_types = ['text/x-strings']
    format = "Apple STRINGS (*.strings)"

    ENCODING = 'UTF-8'

    def _post_compile(self, *args, **kwargs):
        self.compiled_template = self.compiled_template.encode('utf-16')

    @need_resource
    def compile(self, language=None):
        if not language:
            language = self.language

        # pre compile init
        self._pre_compile(language=language)

        self.content = Template.objects.get(resource=self.resource).content
        self.content = self.content.decode(self.ENCODING)
        self._examine_content(self.content)

        stringset = self._get_strings(self.resource)

        for string in stringset:
            trans = self._get_translation(string, language, 5)
            self.content = self._replace_translation(
                "%s_tr" % string.string_hash,
                trans and trans.string or "",
                self.content
            )

        self.compiled_template = self.content
        del self.content
        self._post_compile(language)

    @classmethod
    def accepts(cls, filename=None, mime=None):
        accept = False
        if filename is not None:
            accept |= filename.endswith(".strings")
        if mime is not None:
            accept |= mime in cls.mime_types
        return accept

    @classmethod
    def contents_check(self, filename):
        pass

    def _escape(self, s):
        return s.replace('"', '\\"')

    def _unescape(self, s):
        return s.replace('\\"', '"')

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parse an apple .strings file and create a stringset with
        all entries in the file.

        See
        http://developer.apple.com/library/mac/#documentation/MacOSX/Conceptual/BPInternational/Articles/StringsFiles.html
        for details.
        """
        resource = self.resource
        stringset = StringSet()
        suggestions = StringSet()

        context = ""
        fh = open(self.filename, "r")
        p = re.compile(r'(?P<line>(("(?P<key>[^"\\]*(?:\\.[^"\\]*)*)")|(?P<property>\w+))\s*=\s*"(?P<value>[^"\\]*(?:\\.[^"\\]*)*)"\s*;)', re.U)
        c = re.compile(r'\s*/\*(.|\s)*?\*/\s*', re.U)
        ws = re.compile(r'\s+', re.U)
        try:
            f = fh.read()
            if chardet.detect(f)['encoding'].startswith('UTF-16'):
                f = f.decode('utf-16')
            else:
                f = f.decode(self.ENCODING)
            buf = u""
            end=0
            start = 0
            for i in p.finditer(f):
                start = i.start()
                end_ = i.end()
                line = i.group('line')
                key = i.group('key')
                if not key:
                    key = i.group('property')
                value = i.group('value')
                while end < start:
                    m = c.match(f, end, start) or ws.match(f, end, start)
                    if not m or m.start() != end:
                        raise StringsParseError("Invalid syntax.")
                    if is_source:
                        buf += f[end:m.end()]
                    end = m.end()
                end = end_
                if is_source:
                    if not value.strip():
                        buf += line
                        continue
                    else:
                        line = f[start:end]
                        value = f[i.start('value'):i.end('value')]
                        buf += re.sub(
                            re.escape(value),
                            "%(hash)s_tr" % {'hash': hash_tag(key, context)},
                            line
                        )
                elif not SourceEntity.objects.filter(resource=resource, string=key).exists() or not value.strip():
                    # ignore keys with no translation
                    continue
                stringset.strings.append(GenericTranslation(key,
                    self._unescape(value), rule=5, context=context,
                    pluralized=False, fuzzy=False,
                    obsolete=False)) 
            while len(f[end:]):
                m = c.match(f, end) or ws.match(f, end)
                if not m or m.start() != end:
                    raise StringsParseError("Invalid syntax.")
                if is_source:
                    buf += f[end:m.end()]
                end = m.end()
                if end == 0:
                    break

        except UnicodeDecodeError, e:
            raise StringsParseError(e.message)
        finally:
            fh.close()

        self.stringset=stringset
        self.suggestions=suggestions

        if is_source:
            self.template = str(buf.encode(self.ENCODING))

