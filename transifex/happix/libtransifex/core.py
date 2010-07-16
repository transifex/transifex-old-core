# -*- coding: utf-8 -*-

import copy
import json
import os
import codecs

"""
STRICT flag is used to switch between two parsing modes:
  True - minor bugs in source files are treated fatal
    In case of Qt TS parser this means that buggy location elements will
    raise exceptions.
  False - if we get all necessary information from source files
    we will pass
"""
STRICT=False

class CustomSerializer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Translation):
            d = {
                'source_entity' : obj.source_entity,
                'translation' : obj.translation,
            }
            if obj.occurrences:
                d['occurrences'] = obj.occurrences
            if obj.comments:
                d['comments'] = obj.comments
            if obj.context:
                d['context'] = obj.context
            if obj.rule:
                d['rule'] = obj.rule
            if obj.pluralized:
                d['pluralized'] = obj.pluralized

            return d

        if isinstance(obj, StringSet):
            return {
                #'filename' : obj.filename,
                'target_language' : obj.target_language,
                'strings' : obj.strings,
            }

class ParseError(StandardError):
    pass


class CompileError(StandardError):
    pass


class Parser:
    """
    Base class for writting file parsers for all the I18N types.
    """
    default_encoding = "utf-8"

    @classmethod
    def open(cls, filename = None, root = None, fd = None):
        if filename or fd:
            if not fd:
                if root:
                    relpath = filename
                    if relpath[0] == "/":
                        relpath = relpath[1:]
                    fullpath = os.path.join(root, relpath)
                else:
                    fullpath = filename
                fd = codecs.open( fullpath, "r", cls.default_encoding )
            buf = fd.read()
            if ord(buf[0]) == 0xfeff:
                buf = buf[1:] # Remove byte order marker
            fd.close()
            stringset = cls.parse(buf)
            stringset.filename = filename
            return stringset

    @classmethod
    def accept(cls, filename):
        return False

    @classmethod
    def parse(cls, buf):
        raise Exception("Parser.parse(buf) has to be overridden")

    @classmethod
    def parse_file(cls, filename, is_source=False, lang_rules=None):
        fh = open(filename, "ru")
        return cls.parse(fh.read(), is_source, lang_rules)


class StringSet:
    """
    Store a list of Translation objects for a given language.
    """
    def __init__(self):
        self.strings = []
        self.target_language = None

    def strings_grouped_by_context(self):
        d = {}
        for i in self.strings:
            if i.context in d:
                d[i.context].append(i)
            else:
                d[i.context] = [i,]
        return d

    def to_json(self):
        return json.dumps(self, cls=CustomSerializer)


class Translation:
    """
    Store translations of any kind of I18N type (POT, QT, etc...).

    Parameters:
        source_entity - The original entity found in the source code.
        translation - The related source_entity written in another language.
        context - The related context for the source_entity.
        occurrences - Occurrences of the source_entity from the source code.
        comments - Comments for the given source_entity from the source code.
        rule - Plural rule 0=zero, 1=one, 2=two, 3=few, 4=many or 5=other.
        pluralized - True if the source_entity is a plural entry.
        fuzzy - True if the translation is fuzzy/unfinished
        obsolete - True if the entity is obsolete
    """
    def __init__(self, source_entity, translation, occurrences=None, 
            comments=None, context=None, rule=5, pluralized=False,
            fuzzy=False, obsolete=False):
        self.source_entity = source_entity
        self.translation = translation
        self.context = context
        self.occurrences = occurrences
        self.comments = comments
        self.rule = int(rule)
        self.pluralized = pluralized
        self.fuzzy = fuzzy
        self.obsolete = obsolete

    def __hash__(self):
        if STRICT:
            return hash((self.source_entity, self.translation, 
                self.occurrences))
        else:
            return hash((self.source_entity, self.translation))

    def __eq__(self, other):
        if isinstance(other, self.__class__) and \
            self.source_entity == other.source_entity and \
            self.translation == other.translation and \
            self.context == other.context:
            return True
        return False