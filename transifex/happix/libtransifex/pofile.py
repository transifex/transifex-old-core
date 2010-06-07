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
        # For .pot files the msgid entry must be used as the translation for
        # the related language.
        if filename.endswith(".pot"):
            use_msgid = True
        else:
            use_msgid = False

        for entry in polib.pofile(filename):
            # Get the correct entry messages based in the on its plural and/or
            # the file extention (use_msgid).
            if entry.msgid_plural:
                if use_msgid:
                    messages = [entry.msgid, entry.msgid_plural]
                else:
                    message_keys = entry.msgstr_plural.keys()
                    message_keys.sort()
                    messages = [entry.msgstr_plural[k] for k in message_keys]
            else:
                if use_msgid:
                    messages = [entry.msgid]
                else:
                    messages = [entry.msgstr]

            # Add messages with the correct number (plural)
            for number, msgstr in enumerate(messages):
                if number == 0:
                    msgid = entry.msgid
                else:
                    msgid = entry.msgid_plural
                stringset.strings.append(Translation(msgid, msgstr,
                    context=entry.msgctxt, occurrences=entry.occurrences,
                    number=number))
        return stringset
