# -*- coding: utf-8 -*-

"""
GNU Gettext .PO/.POT file parser/compiler
"""
import polib
from core import StringSet, ParseError, Translation, CompileError, Parser, STRICT

#class ResXmlParseError(ParseError):
    #pass

#class ResXmlCompileError(CompileError):
    #pass

import uuid

class PofileParser(Parser):
    """
    Translate Toolkit is using Gettext C library to parse/create PO files in Python
    TODO: Switch to Gettext C library
    """
    name = "GNU Gettext *.PO/*.POT parser"
    mime_type = "application/x-gettext"
    format = "GNU Gettext Catalog (*.po, *.pot)"

    @classmethod
    def accept(cls, filename):
        return filename.endswith(".po") or filename.endswith(".pot")

    @classmethod
    def compile(cls, stringset):
        pass

    @classmethod
    def parse_file(cls, filename):
        stringset = StringSet()
        if filename.endswith(".pot"):
            use_msgid = True
        else:
            use_msgid = False
        for entry in polib.pofile(filename):
            if use_msgid:
                entry.msgstr = entry.msgid
            stringset.strings.append(Translation(entry.msgid,
                entry.msgstr, context = entry.msgctxt,
                occurrences = entry.occurrences ))
        return stringset
