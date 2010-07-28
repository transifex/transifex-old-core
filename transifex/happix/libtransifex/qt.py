# -*- coding: utf-8 -*-

"""
Qt4 TS file parser for Python
"""

import xml.dom.minidom
from xml.dom.minidom import DOMImplementation
from django.db import transaction
from django.db.models import get_model
from core import StringSet, ParseError, GenericTranslation, CompileError, Handler, STRICT
from txcommon.log import logger
from happix.libtransifex.decorators import *

# Happix models
Resource = get_model('happix', 'Resource')
Translation = get_model('happix', 'Translation')
SourceEntity = get_model('happix', 'SourceEntity')
Storage = get_model('storage', 'StorageFile')

class LinguistParseError(ParseError):
    pass

class LinguistCompileError(CompileError):
    pass

class LinguistHandler(Handler):
    name = "Qt4 TS parser"
    format = "Qt4 Translation XML files (*.ts)"
    mime_type = "application/x-linguist"

    @classmethod
    def accept(cls, filename):
        return filename.endswith(".ts")

    @need_resource
    def compile(self, is_source=False, language = None):
        """
        Method that takes a `language` as and the bound resource as arguments
        and creates the requested translation file. Contents are not saved to
        disk but are held under the ``compiled `` class attribute.
        save2file(filename) needs to be run in order to save all file contents
        to the disk.
        """
        if not language:
            language = self.language

        # Create XML root
        imp = DOMImplementation()
        doctype = imp.createDocumentType(
            qualifiedName='TS',
            publicId=None,
            systemId=None,
        )
        doc = imp.createDocument(None, 'TS', doctype)
        root = doc.documentElement
        root.setAttribute("version", "2.0")
        root.setAttribute("language", language.code)
        doc.appendChild(root)

        # Group source entities by context
        context_stringset = SourceEntity.objects.filter(
            resource = self.resource)
        contexts = context_stringset.values('context').order_by().distinct()
        for c in contexts:
            # Create context elements under which the messages are grouped
            string_context = c['context']
            context = doc.createElement("context")
            context_name = doc.createElement("name")
            context_name.appendChild(doc.createTextNode(string_context))
            context.appendChild(context_name)
            stringset = SourceEntity.objects.filter(
                resource = self.resource,
                context = string_context)
            # If single string instead of list, turn into list
            if not hasattr(stringset, '__iter__'):
                stringset = [ stringset ]
            for string in stringset:
                try:
                    trans = Translation.objects.get(
                        resource = self.resource,
                        source_entity=string,
                        language = language,
                        rule =5)
                except Translation.DoesNotExist:
                    trans = None
                message = doc.createElement("message")
                source = doc.createElement("source")
                translation = doc.createElement("translation")

                if string.pluralized:
                    plural_keys = {}
                    # last rule excluding other(5)
                    last_rule = language.get_pluralrules_numbers()[-2]
                    # Initialize all plural rules up to the last
                    for p in range(0,last_rule):
                        plural_keys[p] = ""
                    plurals = Translation.objects.filter(
                        resource = self.resource,
                        language = language,
                        source_entity = string)
                    for p in plurals:
                        plural_keys[p.rule] =  p.string
                    message.setAttribute('numerus', 'yes')
                    for key in plural_keys.keys():
                        e = doc.createElement("numerusform")
                        e.appendChild(doc.createTextNode(plural_keys[key]))
                        translation.appendChild(e)
                else:
                    translation.appendChild(doc.createTextNode(trans.string if trans else ""))

                source.appendChild(doc.createTextNode(string.string))
                if not trans:
                    translation.setAttribute('type', 'unfinished')

                # If we add the STRING flag the location is not outputed to the
                # file by default. Do we want that?
                #if STRICT:
                if string.occurrences and \
                    string.occurrences != "":
                    for _location in string.occurrences.split(";"):
                        filename, line = _location.split(":")
                        location = doc.createElement("location")
                        location.setAttribute("filename", filename)
                        location.setAttribute("line", line)
                        message.appendChild(location)

                message.appendChild(source)
                message.appendChild(translation)


                context.appendChild(message)

            root.appendChild(context)
        self.compiled = doc.toprettyxml(encoding=self.default_encoding)
        return doc

    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parses QT file and exports all entries as GenericTranslations.
        """
        buf = fh = open(self.filename, "ru").read()
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

        stringset = StringSet()
        # This needed to be commented out due the 'is_source' parameter.
        # When is_source=True we return the value of the <source> node as the 
        # translation for the given file, instead of the <translation> node(s).
        #stringset.target_language = language
        #language = get_attribute(root, "language", die = STRICT)

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
                obsolete, fuzzy = False, False
                messages = []
                if is_source:
                    messages = [(5, sourceString)]
                    if pluralized:
                        try:
                            msgid_plural = getElementByTagName(message,
                                "extra-po-msgid_plural")
                            messages.insert(0, (1,
                                msgid_plural.firstChild.nodeValue))
                        except LinguistParseError:
                            pass

                elif translation and translation.firstChild:
                    if not pluralized:
                        messages = [(5, translation.firstChild.nodeValue)]
                    else:
                        numerusforms = translation.getElementsByTagName('numerusform')
                        if nplural:
                            nplural_file = len(numerusforms)
                            if nplural != nplural_file:
                                logger.error("Passed plural rules has nplurals=%s"
                                    ", but '%s' file has nplurals=%s. String '%s'"
                                    "skipped." % (nplural, self.filename,
                                     nplural_file, sourceString))
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
                        stringset.strings.append(GenericTranslation(sourceString,
                            msg[1], context = context_name, rule=msg[0],
                            occurrences = ";".join(occurrences), 
                            pluralized=pluralized, fuzzy=fuzzy, 
                            obsolete=obsolete))
                i += 1

            self.stringset=stringset
        return


    @need_compiled
    def save2file(self, filename):
        """
        Take the ouput of the compile method and save results to specified file
        """
        try:
            fd=open(filename, 'w')
        except Exception, e:
            raise Exception("Error opening file %s: %s" % ( filename, e))

        fd.write(self.compiled)
        fd.flush()
        fd.close()
