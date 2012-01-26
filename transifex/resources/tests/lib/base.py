# -*- coding: utf-8 -*-
import os
import logging
from django.conf import settings
from django.utils.hashcompat import md5_constructor
from transifex.txcommon.tests import base

class FormatsBaseTestCase(base.BaseTestCase):
    """Base class for tests on supported formats."""

    def setUp(self):
        super(FormatsBaseTestCase, self).setUp()
        logging.disable(logging.CRITICAL)

    def compare_to_actual_file(self, handler, actual_file):
        template = handler.template
        for s in handler.stringset.strings:
            trans = s.translation
            source = s.source_entity
            source = "%(hash)s_tr" % {'hash':md5_constructor(
                    ':'.join([source, ""]).encode('utf-8')).hexdigest()}
            compiler = handler.CompilerClass(handler.resource)
            compiler._examine_content(template)
            template = compiler._replace_translation(
                "%s" % source, trans and trans or "", template
            )
        with open(actual_file, 'r') as f:
            actual_content = f.read()
        self.assertEquals(template, actual_content)

    def get_content_from_file(self, filename, encoding=False):
        """Get content from a file as required by handler's
        bind_content() method"""
        f = open(filename, 'r')
        content = f.read()
        f.close()
        if encoding:
            content = content.decode(encoding)
        return content
