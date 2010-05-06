# -*- coding: utf-8 -*-

"""
Microsoft .NET resources XML (.resx) parser/compiler
"""

import xml.dom.minidom
from xml.dom.minidom import DOMImplementation
from core import StringSet, ParseError, TranslationString, CompileError, Parser, STRICT

class ResXmlParseError(ParseError):
    pass

class ResXmlCompileError(CompileError):
    pass

class ResXmlParser(Parser):
    name = "Microsoft .resx parser"
    mimetype = "text/microsoft-resx"

    @classmethod
    def accept(cls, filename):
        return filename.endswith(".resx")

    @classmethod
    def compile(cls, stringset):
        pass

    @classmethod
    def parse(cls, buf):
        def getElementByTagName(element, tagName, noneAllowed = False):
            elements = element.getElementsByTagName(tagName)
            if not noneAllowed and not elements:
                raise ResXmlParseError("Element '%s' not found!" % tagName)
            if len(elements) > 1:
                raise ResXmlParseError("Multiple '%s' elements found!" % tagName)
            return elements[0]

        def get_inner_text(element, allow_empty=True, die=False):
            if not element:
                raise ResXmlParseError("Element was null")
            if len(element) != 1:
                raise ResXmlParseError("Element '%s' does not contain single"
                    " child" % element.tagName)
            if not element[0] or not element[0].nodeValue:
                raise ResXmlParseError("Element '%s' is null" % element.tagName)
            return element[0].nodeValue

        def get_attribute(element, key, die = False):
            if element.attributes.has_key(key):
                return element.attributes[key].value
            elif die:
                raise ResXmlParseError("Could not find attribute '%s' "\
                    "for element '%s'" % (key, element.tagName))
            else:
                return None

        def clj(s, w):
            return s[:w].replace("\n", " ").ljust(w)

        doc = xml.dom.minidom.parseString(buf)
        
        #if doc.doctype.name != "TS":
            #raise LinguistParseError("Incorrect doctype!")
        root = doc.documentElement
        if root.tagName != "root":
            raise ResXmlParseError("Root element is not 'root'")

        meta = {}
        for resheader in root.getElementsByTagName("resheader"):
            key = get_attribute(resheader, "name", die=True)
            _value = getElementByTagName(resheader, "value")
            if _value and _value.firstChild and _value.firstChild.nodeValue:
                value = _value.firstChild.nodeValue
                meta[key] = value
            else:
                raise ResXmlParseError("Malformed 'resheader' element")
        print meta

#        for data in root.getElementsByTagName("data")
#            source_string = get_attribute(data, "name")
#            translation_string =
        exit(1)