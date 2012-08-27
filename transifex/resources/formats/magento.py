# -*- coding: utf-8 -*-

"""
Magento CSV handler
"""
from __future__ import absolute_import
import os
import re
import codecs
import csv
from cStringIO import StringIO

from transifex.txcommon.log import logger
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import GenericTranslation,\
    STRICT, StringSet, Handler
from transifex.resources.formats.compilation import SimpleCompilerFactory,\
    NormalDecoratorBuilder, Compiler


class CommentedFile(object):
    """
    A File like class to skip comment lines in a CSV file
    and append the comment lines to template_dict['buf']
    """
    def __init__(self, f, template_dict, comment_chars=("#",)):
        self.f = f
        self.comment_chars = comment_chars
        self.template_dict = template_dict

    def next(self):
        line = self.f.next()
        while line.startswith(self.comment_chars):
            self.template_dict['buf'] += line.decode('utf-8')
            line = self.f.next()
        return line

    def __iter__(self):
        return self


class CSVDecoratorBuilder(NormalDecoratorBuilder):
    def __call__(self, translation):
        """Escape the string first including empty strings"""
        return self._escape(translation)


class MagentoCSVCompilerFactory(SimpleCompilerFactory):

    def _get_translation_decorator(self, pseudo_type):
        if pseudo_type is None:
            return CSVDecoratorBuilder(escape_func=self._escape)
        else:
            return PseudoDecoratorBuilder(
                escape_func=self._escape,
                pseudo_func=pseudo_type.compile
            )


class MagentoCSVHandler(MagentoCSVCompilerFactory, Handler):
    """
    Handler for Magento CSV files.
    """
    name = "Magento *.csv handler"
    format = "Magento CSV (*.csv)"
    comment_chars = ('#', ';', )

    @classmethod
    def accepts(cls, filename=None, mime=None):
        accept = False
        if filename is not None:
            accept |= filename.endswith(".csv")
        if mime is not None:
            accept |= mime in cls.mime_types
        return accept

    @classmethod
    def contents_check(self, filename):
        pass

    def _parse(self, is_source=False, lang_rules=None):
        """
        Parse an CSV file and create a stringset with all entries in the file.
        """
        template = u''
        template_dict = {'buf': ''}
        f = StringIO(self.content.encode(self.default_encoding))
        f = CommentedFile(f, template_dict, comment_chars=self.comment_chars)
        csv_reader = csv.reader(f)
        self._find_linesep(self.content)

        for row in csv_reader:
            line = ','.join(['"%s"' % col for col in row]).decode(
                self.default_encoding)
            # Skip empty lines
            # Comment lines have already been skipped and recorded in
            # CommentedFile
            if not line:
                if is_source:
                    template_dict['buf'] += line + self.linesep
                continue
            try:
                source, trans = row
                source = source.decode(self.default_encoding)
                trans = trans.decode(self.default_encoding)
            except ValueError:
                logger.warning('Could not parse line "%s"' % line)
                if is_source:
                    template_dict['buf'] += line + self.linesep
                continue
            context = ""
            if is_source:
                source_hash = "%(hash)s_tr" % {'hash': hash_tag(
                    source, context)}
                escaped_source = self._escape(source)
                template_dict['buf'] += ','.join(
                    [escaped_source, source_hash]) + self.linesep

            self._add_translation_string(source, trans, context=context)
        if is_source:
            template = template_dict['buf'][: -1 * len(self.linesep)]
        return template

    def _escape(self, s):
        return '"%s"' % s.replace('"', '""')
