# -*- coding: utf-8 -*-

""" Wikitext format handler """
import os, re
from itertools import groupby
from transifex.txcommon.log import logger
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import GenericTranslation, Handler, StringSet

class WikiHandler(Handler):
    name = "Wiki handler"
    mime_types = ['text/x-wiki']
    format = "Files extracted from Wikipedia (.wiki)"

    @classmethod
    def accepts(cls, filename=None, mime=None):
        return (filename and filename.endswith('.wiki')) or mime in cls.mime_types

    @classmethod
    def contents_check(self, filename):
        pass

    @classmethod
    def _paragraphs(self, text):
        for k, g in groupby(text.splitlines(True), key=unicode.isspace):
            if not k:
                yield ''.join(g)

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        stringset = StringSet()
        suggestions = StringSet()

        fh = open(self.filename, 'r')
        try:
            buf = fh.read().decode('utf-8')
            for par in self._paragraphs(buf):
                context = ''

                source = trans = par.strip()

                if is_source:
                    source_len = len(source)
                    new_line = re.sub(
                        re.escape(trans),
                        "%(hash)s_tr" % {'hash': hash_tag(source, context)},
                        par
                    )
                    buf = re.sub(re.escape(par), new_line, buf)

                stringset.strings.append(GenericTranslation(source,
                    trans, context=context))
        finally:
            fh.close()

        self.stringset = stringset
        self.suggestions = suggestions

        if is_source:
            self.template = str(buf.encode('utf-8'))