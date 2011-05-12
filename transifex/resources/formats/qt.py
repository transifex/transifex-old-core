# -*- coding: utf-8 -*-

"""
Qt4 TS file parser for Python
"""
import re
import time
import xml.dom.minidom
import xml.parsers.expat
from xml.sax.saxutils import escape as xml_escape
from django.db import transaction
from django.db.models import get_model
from django.utils.translation import ugettext, ugettext_lazy as _
from transifex.txcommon.log import logger
from transifex.txcommon.exceptions import FileCheckError
from transifex.resources.formats.core import StringSet, ParseError, \
    GenericTranslation, CompileError, Handler, STRICT
from suggestions.models import Suggestion
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag

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

def _getText(nodelist):
    rc = []
    for node in nodelist:
        if hasattr(node, 'data'):
            rc.append(node.data)
        else:
            rc.append(node.toxml())
    return ''.join(rc)


class LinguistHandler(Handler):
    name = "Qt4 TS parser"
    format = "Qt4 Translation XML files (*.ts)"
    mime_types = ["application/x-linguist"]

    @classmethod
    def accepts(cls, filename=None, mime=None):
        # TODO better way to handle tests
        # maybe remove None?
        accept = False
        if filename is not None:
            accept |= filename.endswith(".ts")
        if mime is not None:
            accept |= mime in cls.mime_types
        return accept

    @classmethod
    def contents_check(self, filename):
        """
        Check file for XML validity. No DTD checking happens here.
        """
        try:
            parser = xml.parsers.expat.ParserCreate()
            parser.ParseFile(open(filename, "r"))
        except Exception, e:
            raise FileCheckError, ugettext("Your file doesn't seem to contain "\
                "valid xml: %s!" % e )

    def _do_replace(self, original, replacement, text):
        """
        It just does a search and replace inside `text` and replaces all
        occurrences of `original` with `replacement`.
        """
        return re.sub(re.escape(original), xml_escape(replacement,
            {"'": "&apos;", '"': '&quot;'}), text)

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

                # If we have an id for the message use this as the source
                # string, otherwise use the actual source string
                if message.attributes.has_key("id"):
                    sourceString = message.attributes['id'].value
                else:
                    sourceString = _getText(source.childNodes)

                plurals = Translation.objects.filter(
                    source_entity__resource = self.resource,
                    language = language,
                    source_entity__string = sourceString
                ).order_by('rule')

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
                    e.appendChild(doc.createTextNode(xml_escape(plural_keys[key],
                        {"'": "&apos;", '"': '&quot;'})))
                    translation.appendChild(e)

        template_text = doc.toxml()
        esc_template_text = re.sub("'(?=(?:(?!>).)*<\/source>)",
            r"&apos;", template_text)
        esc_template_text = re.sub("'(?=(?:(?!>).)*<\/translation>)",
            r"&apos;", esc_template_text)
        self.compiled_template = esc_template_text

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parses Qt file and exports all entries as GenericTranslations.
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
        if hasattr(doc, 'doctype') and hasattr(doc.doctype, 'name'):
            if doc.doctype.name != "TS":
                raise LinguistParseError("Incorrect doctype!")
        else:
            raise LinguistParseError("Uploaded file has no Doctype!")
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
                try:
                    ec_node = _getElementByTagName(message, "extracomment")
                    extracomment = _getText(ec_node.childNodes)
                except LinguistParseError, e:
                    extracomment = None

                status = None
                if source.firstChild:
                    sourceString = _getText(source.childNodes)
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
                    if translation.attributes.has_key("variants") and \
                      translation.attributes['variants'].value == 'yes':
                        logger.error("Source file has unsupported"
                            " variants.")
                        raise LinguistParseError("Qt Linguist variants are"
                            " not yet supported.")

                    # Skip obsolete strings.
                    if translation.attributes.has_key("type"):
                        status = translation.attributes["type"].value.lower()
                        if status == "obsolete":
                            continue

                    messages = [(5, sourceStringText or sourceString)]
                    # remove unfinished/obsolete attrs from template
                    if translation.attributes.has_key("type"):
                        status = translation.attributes["type"].value.lower()
                        if status == "unfinished":
                            del translation.attributes["type"]
                    if pluralized:
                        try:
                            numerusforms = translation.getElementsByTagName('numerusform')
                            for n,f in enumerate(numerusforms):
                                if numerusforms[n].attributes.has_key("variants") and \
                                  numerusforms[n].attributes['variants'].value == 'yes':
                                    logger.error("Source file has unsupported"
                                        " variants.")
                                    raise LinguistParseError("Source file"
                                        " could not be imported: Qt Linguist"
                                        " variants are not supported.")
                            for n,f in enumerate(numerusforms):
                                if numerusforms[n].attributes.has_key("variants") and \
                                  numerusforms[n].attributes['variants'].value == 'yes':
                                    continue
                            for n,f in enumerate(numerusforms):
                                nf=numerusforms[n]
                                messages.append((nplural[n], _getText(nf.childNodes)
                                    or sourceStringText or sourceString ))
                        except LinguistParseError, e:
                            pass

                elif translation and translation.firstChild:
                    # For messages with variants set to 'yes', we skip them
                    # altogether. We can't support variants at the momment...
                    if translation.attributes.has_key("variants") and \
                      translation.attributes['variants'].value == 'yes':
                        continue

                    # Skip obsolete strings.
                    if translation.attributes.has_key("type"):
                        status = translation.attributes["type"].value.lower()
                        if status == "obsolete":
                            continue

                    if translation.attributes.has_key("type"):
                        status = translation.attributes["type"].value.lower()
                        if status == "unfinished" and\
                          not pluralized:
                            suggestion = GenericTranslation(sourceString,
                                _getText(translation.childNodes),
                                context=context_name,
                                occurrences= ";".join(occurrences))
                            suggestions.strings.append(suggestion)
                        else:
                            logger.error("Element 'translation' attribute "\
                                "'type' is neither 'unfinished' nor 'obsolete'")

                        continue

                    if not pluralized:
                        messages = [(5, _getText(translation.childNodes))]
                    else:
                        numerusforms = translation.getElementsByTagName('numerusform')
                        try:
                            for n,f  in enumerate(numerusforms):
                                if numerusforms[n].attributes.has_key("variants") and \
                                  numerusforms[n].attributes['variants'].value == 'yes':
                                    raise StopIteration
                        except StopIteration:
                            continue
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
                            nf=numerusforms[n]
                            if nf.firstChild:
                                messages.append((nplural[n], _getText(nf.childNodes)))

                    # NB! If <translation> doesn't have type attribute, it means that string is finished

                if sourceString and messages:
                    for msg in messages:
                        stringset.strings.append(GenericTranslation(sourceString,
                            msg[1], context = context_name, rule=msg[0],
                            occurrences = ";".join(occurrences),
                            pluralized=pluralized, fuzzy=fuzzy,
                            comment=extracomment, obsolete=obsolete))
                i += 1

                if is_source:
                    if sourceString is None:
                        continue
                    if message.attributes.has_key("numerus") and \
                        message.attributes['numerus'].value=='yes':
                            numerusforms = translation.getElementsByTagName('numerusform')
                            for n,f in enumerate(numerusforms):
                                f.appendChild(doc.createTextNode(
                                        "%(hash)s_pl_%(key)s" %
                                        {
                                            'hash': hash_tag(sourceString, context_name),
                                            'key': n
                                        }
                                ))
                    else:
                        if not translation:
                            translation = doc.createElement("translation")

                        # Delete all child nodes. This is usefull for xml like
                        # strings (eg html) where the translation text is split
                        # in multiple nodes.
                        translation.childNodes = []

                        translation.appendChild(doc.createTextNode(
                                ("%(hash)s_tr" % {'hash': hash_tag(sourceString, context_name)})
                        ))

            if is_source:
                # Ugly fix to revert single quotes back to the escaped version
                template_text = doc.toxml().encode('utf-8')
                esc_template_text = re.sub("'(?=(?:(?!>).)*<\/source>)",
                    r"&apos;", template_text)
                self.template = str(esc_template_text)

            self.suggestions = suggestions
            self.stringset=stringset
        return
