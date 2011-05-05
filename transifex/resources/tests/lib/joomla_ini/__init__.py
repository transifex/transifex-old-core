# -*- coding: utf-8 -*-

import os
from transifex.resources.formats.joomla import JoomlaINIHandler
from transifex.languages.models import Language
from transifex.resources.tests.lib.base import FormatsBaseTestCase

class TestJoomlaIni(FormatsBaseTestCase):
    """Tests for Joomla init files."""

    def setUp(self):
        super(TestJoomlaIni, self).setUp()
        self.file = os.path.join(os.path.dirname(__file__), 'example1.6.ini')
        self.parser = JoomlaINIHandler(self.file)
        self.parser.set_language(Language.objects.by_code_or_alias("en_US"))

    def test_accept(self):
        self.assertTrue(self.parser.accepts(self.file))

    def test_quote_removal(self):
        self.parser.parse_file(is_source=True)
        for s in self.parser.stringset.strings:
            self.assertFalse(s.translation.startswith('"'))
        self.compare_to_actual_file(self.parser, self.file)

    def test_quotes_on_previous_version(self):
        file_ = os.path.join(os.path.dirname(__file__), 'example1.5.ini')
        self.parser.bind_file(file_)
        self.parser.parse_file(is_source=True)
        self.compare_to_actual_file(self.parser, file_)

