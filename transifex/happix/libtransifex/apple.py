# -*- coding: utf-8 -*-

"""
Apple Localizable.strings file parser class for Python
"""
from core import Parser, ParseError, TranslationString, CompileError, StringSet

class AppleParseError(ParseError):
    pass

class AppleCompileError(CompileError):
    pass

DEBUG=True
STRICT=True

class AppleStringsParser(Parser):
    name = "Apple .strings parser"
    default_encoding = "utf-8" # or theoretically utf-16

    @classmethod
    def accept(cls, filename):
        return filename.endswith("/Localizable.strings")

    @classmethod
    def compile(cls, stringset):
        buf = u""
        for i in stringset.strings:
            # TODO: Escape chars: \n \\ \" etc
            buf += u"\"%s\" = \"%s\" ;\n" % (i.source_string, i.translation_string)
        return buf

    @classmethod
    def parse(cls, buf):
        """
        An Apple .strings file looks like this:
        /* Some comments
         * May span multiple lines */
        "source_string_identifier" = "Translated string" ; # Prepended comments
        "source_string_identifier" = "More translated string" ;
        # One line comments
        "source_string_identifier" = "Even more translated String" ;

        """
        stringset = StringSet()
        newline = ['\n','\r']
        whitespace = [' ', '\t'] + newline
        i = -1
        state = None # None means that we don't know current context
        block = ""
        stack = []
        line_number = 1
        row_number = 0
        while i < len(buf)-2:
            i += 1
            cc = buf[i:i+2] # Pop two chars
            a,b=cc # Split them

            if a == "\n":
                line_number += 1
                row_number = 0
            row_number += 1

            # If we don't know the context then drop all whitespace
            if not state and a in whitespace:
                continue

            # Commenting with /*  */
            if cc == "/*" and not state:
                state = "comment"
                continue
            if state == "comment":
                if cc == "*/":
                    i += 1
                    state = None
                    block = ""
                continue

            # Commenting with #
            if a == "#" and not state:
                state = "comment#"
                continue
            if state == "comment#":
                if a in newline:
                    state = None
                continue

            # Double quotes switch to string state
            if a == "\"":
                if state == "string":
                    stack.append(block)
                    block = ""
                    state = None
                else:
                    state = "string"
                continue
            if state == "string":
                block += a
                continue

            # Stacking strings and popping
            if len(stack) == 1 and a == '=':
                continue
            if len(stack) == 2 and a == ';':
                key, value = stack
                stringset.strings.append(TranslationString(key, value))
                stack = []
                continue

            # In case we end up here we have a syntax error
            raise AppleParseError("Syntax error, unexpected character '%c' (0x%02x) at line %i row %i" % (a, ord(a), line_number, row_number))
        return stringset