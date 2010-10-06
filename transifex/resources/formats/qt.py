# -*- coding: utf-8 -*-

"""
Qt4 TS file parser for Python
"""
from hashlib import md5
import time
import xml.dom.minidom
from django.db import transaction
from django.db.models import get_model
from txcommon.log import logger
from resources.formats.core import StringSet, ParseError, \
    GenericTranslation, CompileError, Handler, STRICT
from suggestions.models import Suggestion
from resources.formats.decorators import *

# Resources models
Resource = get_model('resources', 'Resource')
Translation = get_model('resources', 'Translation')
SourceEntity = get_model('resources', 'SourceEntity')
Storage = get_model('storage', 'StorageFile')

class LinguistParseError(ParseError):
    pass

class LinguistCompileError(CompileError):
    pass

def _getElementByTagName(element, tagName, noneAllowed = False):
    elements = element.getElementsByTagName(tagName)
    if not noneAllowed and not elements:
        raise LinguistParseError("Element '%s' not found!" % tagName)
    if len(elements) > 1:
        raise LinguistParseError("Multiple '%s' elements found!" % tagName)
    return elements[0]

def _get_attribute(element, key, die = False):
    if element.attributes.has_key(key):
        return element.attributes[key].value
    elif die:
        raise LinguistParseError("Could not find attribute '%s' "\
            "for element '%s'" % (key, element.tagName))
    else:
        return None


class LinguistHandler(Handler):
    name = "Qt4 TS parser"
    format = "Qt4 Translation XML files (*.ts)"
    mime_types = ["application/x-linguist"]

    @classmethod
    def accept(cls, filename=None, mime=None):
        return filename.endswith(".ts") or mime in cls.mime_types

    @classmethod
    def contents_check(self, filename):
        logger.debug("qt: The 'contents_check' method is not implemented!")

    def _post_compile(self, *args, **kwargs):
        """
        """
        if hasattr(kwargs,'language'):
            language = kwargs['language']
        else:
            language = self.language

        doc = xml.dom.minidom.parseString(self.compiled_template)
        root = doc.documentElement
        root.attributes["language"] = language.code

        for message in doc.getElementsByTagName("message"):
            if message.attributes.has_key("numerus") and \
                message.attributes['numerus'].value=='yes':
                source = _getElementByTagName(message, "source")
                translation = _getElementByTagName(message, "translation")
                numerusforms = message.getElementsByTagName('numerusform')
                translation.childNodes  = []

                plurals = Translation.objects.filter(
                    source_entity__resource = self.resource,
                    language = language,
                    source_entity__string = source.firstChild.toxml())
                plural_keys = {}
                # last rule excluding other(5)
                lang_rules = language.get_pluralrules_numbers()
                # Initialize all plural rules up to the last
                for p,n in enumerate(lang_rules):
                    plural_keys[p] = ""
                for p,n in enumerate(plurals):
                    plural_keys[p] = n.string
                message.setAttribute('numerus', 'yes')
                for key in plural_keys.keys():
                    e = doc.createElement("numerusform")
                    e.appendChild(doc.createTextNode(plural_keys[key]))
                    translation.appendChild(e)

        self.compiled_template = doc.toxml()

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parses QT file and exports all entries as GenericTranslations.
        """
        fh = open(self.filename, "ru")
        buf = fh.read()
        fh.close()

        def clj(s, w):
            return s[:w].replace("\n", " ").ljust(w)

        if lang_rules:
            nplural = len(lang_rules)
        else:
            nplural = self.language.get_pluralrules_numbers()

        doc = xml.dom.minidom.parseString(buf)
        if doc.doctype.name != "TS":
            raise LinguistParseError("Incorrect doctype!")
        root = doc.documentElement
        if root.tagName != "TS":
            raise LinguistParseError("Root element is not 'TS'")

        stringset = StringSet()
        suggestions = StringSet()
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
            context_name_element = _getElementByTagName(context, "name")
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

                source = _getElementByTagName(message, "source")
                translation = _getElementByTagName(message, "translation")

                status = None
                if source.firstChild:
                    sourceString = source.firstChild.toxml()
                else:
                    sourceString = None # WTF?

                # Check whether the message is using logical id
                if message.attributes.has_key("id"):
                    sourceStringText = sourceString
                    sourceString = message.attributes['id'].value
                else:
                    sourceStringText = None

                same_nplural = True
                obsolete, fuzzy = False, False
                messages = []

                if is_source:
                    messages = [(5, sourceStringText or sourceString)]
                    # remove unfinished/obsolete attrs from template
                    if translation.attributes.has_key("type"):
                        status = translation.attributes["type"].value.lower()
                        if status in ["unfinished", "obsolete"]:
                            del translation.attributes["type"]
                    if pluralized:
                        try:
                            numerusforms = translation.getElementsByTagName('numerusform')
                            for n,f  in enumerate(numerusforms):
                                nf=numerusforms[n].firstChild
                                if nf:
                                    messages.append((nplural[n], nf.toxml()))
                        except LinguistParseError:
                            pass

                elif translation and translation.firstChild:
                    if translation.attributes.has_key("type"):
                        status = translation.attributes["type"].value.lower()
                        if status in ["unfinished", "obsolete"] and\
                          not pluralized:
                            suggestion = GenericTranslation(sourceString,
                                translation.firstChild.toxml(),
                                context=context_name,
                                occurrences= ";".join(occurrences))
                            suggestions.strings.append(suggestion)
                        else:
                            logger.error("Element 'translation' attribute "\
                                "'type' isn't either 'unfinished' or 'obsolete'")

                        continue

                    if not pluralized:
                        messages = [(5, translation.firstChild.toxml())]
                    else:
                        numerusforms = translation.getElementsByTagName('numerusform')
                        if nplural:
                            nplural_file = len(numerusforms)
                            if len(nplural) != nplural_file:
                                logger.error("Passed plural rules has nplurals=%s"
                                    ", but '%s' file has nplurals=%s. String '%s'"
                                    "skipped." % (nplural, self.filename,
                                     nplural_file, sourceString))
                                same_nplural = False
                        else:
                            same_nplural = False

                        if not same_nplural:
                            # If we're missing plurals, skip them altogether
                            continue

                        for n,f  in enumerate(numerusforms):
                            nf=numerusforms[n].firstChild
                            if nf:
                                messages.append((nplural[n], nf.toxml()))

                    # NB! If <translation> doesn't have type attribute, it means that string is finished

                if sourceString and messages:
                    for msg in messages:
                        stringset.strings.append(GenericTranslation(sourceString,
                            msg[1], context = context_name, rule=msg[0],
                            occurrences = ";".join(occurrences), 
                            pluralized=pluralized, fuzzy=fuzzy, 
                            obsolete=obsolete))
                i += 1

                if is_source:
                    if message.attributes.has_key("numerus") and \
                        message.attributes['numerus'].value=='yes':
                            numerusforms = translation.getElementsByTagName('numerusform')
                            for n,f in enumerate(numerusforms):
                                f.firstChild.nodeValue = ("%(hash)s_pl_%(key)s" %
                                    {'hash': md5(sourceString.encode('utf-8')).hexdigest(),
                                     'key': n})
                    else:
                        if translation and translation.firstChild:
                            translation.firstChild.data = ("%(hash)s_tr" % 
                                {'hash':md5(sourceString.encode('utf-8')).hexdigest()})
                        else:
                            if not translation:
                                translation = doc.createElement("translation")

                            translation.appendChild(doc.createTextNode(
                                ("%(hash)s_tr" % {'hash':md5(sourceString.encode('utf-8')).hexdigest()})))


            if is_source:
                self.template = str(doc.toxml())


            self.suggestions = suggestions
            self.stringset=stringset
        return
