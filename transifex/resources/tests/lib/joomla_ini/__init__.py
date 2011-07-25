# -*- coding: utf-8 -*-

import os
from transifex.languages.models import Language
from transifex.resources.models import Resource
from transifex.resources.formats.joomla import JoomlaINIHandler
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
        self.assertTrue(self.parser.accepts(mime='text/x-joomla-ini'))

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

    def test_newlines(self):
        file_ = os.path.join(os.path.dirname(__file__), 'newline.ini')
        r = Resource.objects.create(
            slug="joomla", name="Joomla", i18n_type="INI",
            source_language=Language.objects.by_code_or_alias('en'),
            project=self.project
        )
        self.parser.bind_file(file_)
        self.parser.bind_resource(r)
        self.parser.parse_file(is_source=True)
        self.parser.save2db(is_source=True)
        self.parser.compile()
        self.assertTrue(r'\n' in self.parser.compiled_template)

