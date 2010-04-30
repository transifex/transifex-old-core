# -*- coding: utf-8 -*-

"""
Qt4 TS file parser for Python
"""

import xml.dom.minidom
from xml.dom.minidom import DOMImplementation
from core import StringSet, ParseError, TranslationString, CompileError, Parser, STRICT

class LinguistParseError(ParseError):
    pass

class LinguistCompileError(CompileError):
    pass

class LinguistParser(Parser):
    name = "Qt4 TS parser"
    @classmethod
    def accept(cls, filename):
        return filename.endswith(".ts")

    @classmethod
    def compile(cls, stringset):
        imp = DOMImplementation()
        doctype = imp.createDocumentType(
            qualifiedName='TS',
            publicId=None, 
            systemId=None,
        )
        doc = imp.createDocument(None, 'TS', doctype)
        root = doc.documentElement
        root.setAttribute("version", "2.0")
        root.setAttribute("language", stringset.target_language)
        doc.appendChild(root)
        for _context_name, _context in stringset.strings_grouped_by_context().iteritems():
            context = doc.createElement("context")
            context_name = doc.createElement("name")
            context_name.appendChild(doc.createTextNode(_context_name))
            context.appendChild(context_name)
            for _message in _context:
                message = doc.createElement("message")
                source = doc.createElement("source")
                translation = doc.createElement("translation")

                source.appendChild(doc.createTextNode(_message.source_string))
                translation.appendChild(doc.createTextNode(_message.translation_string))
                
                message.appendChild(source)
                message.appendChild(translation)

                if STRICT:
                    if _message.occurrences and \
                        _message.occurrences != "":
                        for _location in _message.occurrences.split(";"):
                            filename, line = _location.split(":")
                            location = doc.createElement("location")
                            location.setAttribute("filename", filename)
                            location.setAttribute("line", line)
                            message.appendChild(location)
                context.appendChild(message)
                
            root.appendChild(context)
        return doc.toxml("UTF-8")
        #return doc.toprettyxml(indent="  ", newl="\n", encoding="UTF-8")

    @classmethod
    def parse(cls, buf):
        def getElementByTagName(element, tagName, noneAllowed = False):
            elements = element.getElementsByTagName(tagName)
            if not noneAllowed and not elements:
                raise LinguistParseError("Element '%s' not found!" % tagName)
            if len(elements) > 1:
                raise LinguistParseError("Multiple '%s' elements found!" % tagName)
            return elements[0]

        def get_attribute(element, key, die = False):
            if element.attributes.has_key(key):
                return element.attributes[key].value
            elif die:
                raise LinguistParseError("Could not find attribute '%s' "\
                    "for element '%s'" % (key, element.tagName))
            else:
                return None

        def clj(s, w):
            return s[:w].replace("\n", " ").ljust(w)

        doc = xml.dom.minidom.parseString(buf)
        if doc.doctype.name != "TS":
            raise LinguistParseError("Incorrect doctype!")
        root = doc.documentElement
        if root.tagName != "TS":
            raise LinguistParseError("Root element is not 'TS'")

        language = get_attribute(root, "language", die = True)

        stringset = StringSet()
        stringset.target_language = language

        i = 1
        # There can be many <message> elements, they might have
        # 'encoding' or 'numerus' = 'yes' | 'no' attributes 
        # if 'numerus' = 'yes' then 'translation' element contains 'numerusform' elements
        for context in root.getElementsByTagName("context"):
            context_name_element = getElementByTagName(context, "name")
            if context_name_element.firstChild:
                context_name = context_name_element.firstChild.nodeValue or ''
            else:
                context_name = ''

            for message in context.getElementsByTagName("message"):
                occurrences = []
                # NB! There can be zero to many <location> elements, but all 
                # of them must have 'filename' and 'line' attributes
                for location in message.getElementsByTagName("location"):
                    if location.attributes.has_key("filename") and \
                        location.attributes.has_key("line"):
                        occurrences.append("%s:%i" % (
                            location.attributes["filename"].value,
                            int(location.attributes["line"].value)))
                    elif STRICT:
                        raise LinguistParseError("Malformed 'location' element")

                source = getElementByTagName(message, "source")
                translation = getElementByTagName(message, "translation")
                
                status = None
                if source.firstChild:
                    sourceString = source.firstChild.nodeValue
                else:
                    sourceString = None # WTF?

                if translation and translation.firstChild:
                    translationString = translation.firstChild.nodeValue
                    if translation.attributes.has_key("type"):
                        status = translation.attributes["type"].value
                        if not status.lower() in ["unfinished", "obsolete"]:
                            raise LinguistParseError("Element 'translation' attribute "\
                                "'type' isn't either 'unfinished' or 'obsolete'")
                    # NB! If <translation> doesn't have type attribute, it means that string is finished
                else:
                    translationString = None # WTF?

                if sourceString and translationString:
                    stringset.strings.append(TranslationString(sourceString, 
                        translationString, context = context_name,
                        occurrences = ";".join(occurrences) ))
                i += 1
        return stringset
