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
from resources.libtransifex.core import (StringSet, ParseError,
    GenericTranslation, CompileError, Handler, STRICT)
from resources.libtransifex.decorators import *

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
    mime_type = "application/x-linguist"

    @classmethod
    def accept(cls, filename):
        return filename.endswith(".ts")

    @classmethod
    def contents_check(self, filename):
        logger.debug("qt: The 'contents_check' method not implemented!")

    def _post_compile(self, *args, **kwargs):
        """
        """
        if hasattr(kwargs,'language'):
            language = kwargs['language']
        else:
            language = self.language

        doc = xml.dom.minidom.parseString(self.compiled_template)
        for message in doc.getElementsByTagName("message"):
            if message.attributes.has_key("numerus") and \
                message.attributes['numerus'].value=='yes':
                source = _getElementByTagName(message, "source")
                translation = _getElementByTagName(message, "translation")
                numerusforms = message.getElementsByTagName('numerusform')

                plurals = Translation.objects.filter(
                    resource = self.resource,
                    language = language,
                    source_entity__string = source.firstChild.toxml())
                plural_keys = {}
                # last rule excluding other(5)
                last_rule = language.get_pluralrules_numbers()[-2]
                # Initialize all plural rules up to the last
                for p in range(0,last_rule):
                    plural_keys[p] = ""
                plural_nodes = translation.childNodes[:]
                for node in plural_nodes:
                    translation.removeChild(node)
                for p in plurals:
                    plural_keys[p.rule] =  p.string
                message.setAttribute('numerus', 'yes')
                for key in plural_keys.keys():
                    e = doc.createElement("numerusform")
                    e.appendChild(doc.createTextNode(plural_keys[key]))
                    translation.appendChild(e)

        self.compiled_template = doc.toxml()

    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parses QT file and exports all entries as GenericTranslations.
        """
        buf = fh = open(self.filename, "ru").read()


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

                same_nplural = True
                obsolete, fuzzy = False, False
                messages = []

                if is_source:
                    messages = [(5, sourceString)]
                    if pluralized:
                        try:
                            numerusforms = translation.getElementsByTagName('numerusform')
                            plural_keys = [n for n, f in enumerate(numerusforms)]
                            # If we want to support many source languages we
                            # need to find a way to handle plural mapping. One
                            # way to do it is to store a dict for each lang
                            # with a mapping of each number range(0,5) goes to
                            # which plural form. For english it'd be something
                            # like {'0':'1', '1': '5'}
                            # XXX: Temp solution for english lang
                            pl_map = {0:1, 1: 5}
                            for n, rule in enumerate(plural_keys):
                                nf=numerusforms[n].firstChild
                                if nf:
                                    messages.append((pl_map[rule], nf.toxml()))

                            # What was this?
#                            msgid_plural = _getElementByTagName(message,
#                                "extra-po-msgid_plural")
#                            messages.insert(0, (1,
#                                msgid_plural.firstChild.toxml()))
                        except LinguistParseError:
                            pass

                elif translation and translation.firstChild:
                    if not pluralized:
                        messages = [(5, translation.firstChild.toxml())]
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
                                messages.append((rule, nf.toxml()))

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
                self.template = doc.toxml()


            self.stringset=stringset
        return
