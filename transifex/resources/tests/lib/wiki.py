# -*- coding: utf-8 -*-

from django.test import TestCase
from resources.formats.wiki import WikiHandler


class TestWikiHandler(TestCase):

    def test_parse_wiki_text(self):
        handler = WikiHandler()

        content = "Text {{italics|is}}\n\nnew {{italics|par\n\npar}}.\n\nTers"
        handler._parse(content)
        self.assertEquals(len(handler.stringset.strings), 3)
        content = "Text {{italics|is}}\n\n\n\nnew {{italics|par\n\npar}}.\n\nTers"
        handler._parse(content)
        self.assertEquals(len(handler.stringset.strings), 3)
