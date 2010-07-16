# -*- coding: utf-8 -*-

"""
Qt4 TS file parser for Python
"""

import xml.dom.minidom
from xml.dom.minidom import DOMImplementation
from core import StringSet, ParseError, Translation, CompileError, Parser, STRICT

class LinguistParseError(ParseError):
    pass

class LinguistCompileError(CompileError):
    pass

class LinguistParser(Parser):
    name = "Qt4 TS parser"
    format = "Qt4 Translation XML files (*.ts)"
    mime_type = "application/x-linguist"
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

                source.appendChild(doc.createTextNode(_message.source_entity))
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
    def parse(cls, buf, is_source, lang_rules):
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

        if lang_rules:
            nplural = len(lang_rules)
        else:
            nplural = None

        doc = xml.dom.minidom.parseString(buf)
        if doc.doctype.name != "TS":
            raise LinguistParseError("Incorrect doctype!")
        root = doc.documentElement
        if root.tagName != "TS":
            raise LinguistParseError("Root element is not 'TS'")

        language = get_attribute(root, "language", die = STRICT)

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

                pluralized = False
                if message.attributes.has_key("numerus") and \
                    message.attributes['numerus'].value=='yes':
                    pluralized = True

                source = getElementByTagName(message, "source")
                translation = getElementByTagName(message, "translation")

                status = None
                if source.firstChild:
                    sourceString = source.firstChild.nodeValue
                else:
                    sourceString = None # WTF?

                same_nplural = True
                messages = []
                if translation and translation.firstChild:
                    if not pluralized:
                        messages = [(5, translation.firstChild.nodeValue)]
                    else:
                        numerusforms = translation.getElementsByTagName('numerusform')
                        if nplural:
                            nplural_file = len(numerusforms)
                            if nplural != nplural_file:
                                logger.error("Passed plural rules has nplurals=%s"
                                    ", but '%s' file has nplurals=%s. String '%s'"
                                    "skipped." % (nplural, filename, nplural_file,
                                    entry.msgid))
                                same_nplural = False
                        else:
                            same_nplural = False

                        if not same_nplural:
                            plural_keys = [n for n, f in enumerate(numerusforms)]
                        else:
                            plural_keys = lang_rules

                        for n, rule in enumerate(plural_keys):
                            nf=numerusforms[n].firstChild
                            if nf:
                                messages.append((rule, nf.nodeValue))

                    obsolete, fuzzy = False, False
                    if translation.attributes.has_key("type"):
                        status = translation.attributes["type"].value.lower()
                        if status in ["unfinished", "obsolete"]:
                            if status == 'unfinished':
                                fuzzy = True
                            else:
                                obsolete = True
                        else:
                            raise LinguistParseError("Element 'translation' attribute "\
                                "'type' isn't either 'unfinished' or 'obsolete'")
                    # NB! If <translation> doesn't have type attribute, it means that string is finished

                if sourceString and messages:
                    for msg in messages:
                        stringset.strings.append(Translation(sourceString,
                            msg[1], context = context_name, rule=msg[0],
                            occurrences = ";".join(occurrences), 
                            pluralized=pluralized, fuzzy=fuzzy, 
                            obsolete=obsolete))
                i += 1
        return stringset
