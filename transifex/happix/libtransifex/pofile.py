# -*- coding: utf-8 -*-

"""
GNU Gettext .PO/.POT file parser/compiler
"""
import polib
from core import StringSet, ParseError, Translation, CompileError, Parser, STRICT
from txcommon.log import logger

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
    def parse_file(cls, filename, lang_rules=None):
        stringset = StringSet()
        # For .pot files the msgid entry must be used as the translation for
        # the related language.
        if filename.endswith(".pot"):
            ispot = True
        else:
            ispot = False

        if lang_rules:
            nplural = len(lang_rules)
        else:
            nplural = None

        for entry in polib.pofile(filename):
            pluralized = False
            same_nplural = True

            if entry.msgid_plural:
                pluralized = True
                if ispot:
                    # English plural rules
                    messages = [(1, entry.msgid),
                                (5, entry.msgid_plural)]
                else:
                    message_keys = entry.msgstr_plural.keys()
                    message_keys.sort()
                    nplural_file = len(message_keys)
                    messages = []
                    if nplural:
                        if nplural != nplural_file:
                            logger.error("Language '%s' has nplurals=%s, but"
                                " '%s' file has nplurals=%s. String '%s'"
                                "skipped." % (language, nplural, filename, 
                                nplural_file, entry.msgid))
                            same_nplural = False
                    else:
                        same_nplural = False

                    if not same_nplural:
                        plural_keys = message_keys
                    else:
                        plural_keys = lang_rules

                    for n, rule in enumerate(plural_keys):
                        messages.append((rule, entry.msgstr_plural['%s' % n]))
            else:
                # Not pluralized, so no plural rules. Use 5 as 'other'.
                if ispot:
                    messages = [(5, entry.msgid)]
                else:
                    messages = [(5, entry.msgstr)]

            # Add messages with the correct number (plural)
            for number, msgstr in enumerate(messages):
                translation = Translation(entry.msgid, msgstr[1], 
                    context=entry.msgctxt, occurrences=entry.occurrences, 
                    rule=msgstr[0], pluralized=pluralized)

                stringset.strings.append(translation)
        return stringset
