# -*- coding: utf-8 -*-

"""
Mozilla properties file handler/compiler
"""

from __future__ import absolute_import
import os, re
from django.utils.hashcompat import md5_constructor
from transifex.txcommon.log import logger
from transifex.resources.models import SourceEntity
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import Handler, ParseError, CompileError
from transifex.resources.formats.resource_collections import StringSet, \
        GenericTranslation
from transifex.resources.formats.properties import PropertiesHandler, \
        PropertiesParseError, PropertiesCompileError, PropertiesCompiler


class MozillaPropertiesParseError(PropertiesParseError):
    pass


class MozillaPropertiesCompileError(PropertiesCompileError):
    pass


class MozillaPropertiesHandler(PropertiesHandler):
    name = "Mozilla *.PROPERTIES file handler"
    format = "Mozilla PROPERTIES (*.properties)"
    method_name = 'MOZILLAPROPERTIES'
    format_encoding = 'UTF-8'

    HandlerParseError = MozillaPropertiesParseError
    HandlerCompileError = MozillaPropertiesCompileError
    CompilerClass = PropertiesCompiler

    def _escape(self, s):
        return (s.replace('\\', r'\\')
                 .replace('\n', r'\n')
                 .replace('\r', r'\r')
                 .replace('\t', r'\t')
        )

    def _unescape(self, s):
        return (s.replace(r'\n', '\n')
                 .replace(r'\r', '\r')
                 .replace(r'\t', '\t')
                 .replace(r'\\', '\\')
        )

    def _visit_value(self, value):
        if value:
            return re.sub(r'\\[uU]([0-9A-Fa-f]{4})',
                    lambda m: unichr(int(m.group(1), 16)), value)
        else:
            return value
