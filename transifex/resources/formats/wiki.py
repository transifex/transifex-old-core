# -*- coding: utf-8 -*-

""" Wikitext format handler """
import os, re
from itertools import groupby
from transifex.txcommon.log import logger
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import GenericTranslation, Handler, \
        StringSet, ParseError, CompileError


class WikiParseError(ParseError):
    pass


class WikiCompileError(CompileError):
    pass


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

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        assert is_source
        try:
            fh = open(self.filename, 'r')
            try:
                buf = fh.read().decode('utf-8')
            finally:
                fh.close()
            self._parse(buf)
        except Exception, e:
            logger.error("Error in wiki text: %s" % e, exc_info=True)
            raise WikiError(unicode(e))

    def _parse(self, content):
        stringset = StringSet()
        suggestions = StringSet()

        par_splitter = "\n\n"
        template_open = "{{"
        template_ends = "}}"

        template = content
        context = ''

        prev_split_pos = 0
        prev_text_pos = 0
        while 1:
            par_pos = content.find(par_splitter, prev_split_pos)
            t_open_pos = content.find(template_open, prev_split_pos)
            if prev_text_pos == -1:
                break
            elif par_pos == -1 and t_open_pos == -1:
                # end of document
                source = trans = content[prev_text_pos:].strip()
                prev_text_pos = -1
            elif par_pos < t_open_pos or t_open_pos == -1:
                source = trans = content[prev_text_pos:par_pos].strip()
                prev_split_pos = prev_text_pos = par_pos + 2
            else:
                t_end_pos = content.find(template_ends, prev_split_pos)
                prev_split_pos = t_end_pos
                continue

            source_len = len(source)
            template = re.sub(
                re.escape(trans),
                "%(hash)s_tr" % {'hash': hash_tag(source, context)},
                template
            )
            stringset.strings.append(GenericTranslation(source,
                trans, context=context))

        self.stringset = stringset
        self.suggestions = suggestions
        self.template = str(template.encode('utf-8'))
