# -*- coding: utf-8 -*-
from __future__ import with_statement
from mock import patch
import os
import logging
from django.conf import settings
from django.utils.hashcompat import md5_constructor
from transifex.txcommon.tests import base
from transifex.resources.formats.compilation import \
        NormalDecoratorBuilder as Decorator
from transifex.resources.formats.utils.hash_tag import hash_tag


class FormatsBaseTestCase(base.BaseTestCase):
    """Base class for tests on supported formats."""

    def setUp(self):
        super(FormatsBaseTestCase, self).setUp()

    def compare_to_actual_file(self, handler, actual_file):
        template = handler.template
        compiler = handler.CompilerClass(handler.resource)
        compiler._tdecorator = Decorator(escape_func=handler._escape)
        compiler._examine_content(handler.template)
        compiler.language = handler.language
        sources = [
            (idx, "%s" % hash_tag(s.source_entity, ""))
            for idx, s in enumerate(handler.stringset.strings)
        ]
        translations = dict([
            (idx, s.translation)
            for idx, s in enumerate(handler.stringset.strings)
        ])
        with patch.object(compiler, '_get_source_strings') as smock:
            with patch.object(compiler, '_tset', create=True) as tmock:
                smock.return_value = sources
                tmock.return_value = translations
                compiler._compile(handler.template)
                template = compiler.compiled_template
        with open(actual_file, 'r') as f:
            actual_content = f.read()
        self.assertEquals(template, actual_content)

    def get_translation(self, t, compiler):
        if not t:
            return ""
        return t

    def get_content_from_file(self, filename, encoding=False):
        """Get content from a file as required by handler's
        bind_content() method"""
        f = open(filename, 'r')
        content = f.read()
        f.close()
        if encoding:
            content = content.decode(encoding)
        return content
