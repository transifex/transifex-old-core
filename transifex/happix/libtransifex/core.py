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
        if isinstance(obj, TranslationString):
            d = {
                'source_string' : obj.source_string,
                'translation_string' : obj.translation_string,
            }
            if obj.occurrences:
                d['occurrences'] = obj.occurrences
            if obj.comments:
                d['comments'] = obj.comments
            if obj.context:
                d['context'] = obj.context
            return d

        if isinstance(obj, StringSet):
            return {
                'filename' : obj.filename,
                'target_language' : obj.target_language,
                'strings' : obj.strings,
            }

class ParseError(StandardError):
    pass

class CompileError(StandardError):
    pass

class TranslationString:
    def __init__(self, source_string, translation_string,
        occurrences = None, comments = None, context = None):
        self.source_string = source_string
        self.translation_string = translation_string
        self.occurrences = occurrences
        self.comments = comments
        self.context = context

    #def serialize(self):
        #d = {
            #'source_string' : self.source_string,
            #'translation_string' : self.translation_string,
        #}
        #if self.occurrences:
            #d['occurrences'] = self.occurrences
        #if self.comment:
            #d['comments'] = self.comment
        #d['context'] = self.context
        #return d

    def __hash__(self):
        if STRICT:
            return hash((self.source_string, self.translation_string, 
                self.occurrences))
        else:
            return hash((self.source_string, self.translation_string))

    def __eq__(self, other):
        if isinstance(other, self.__class__) and \
            self.source_string == other.source_string and \
            self.translation_string == other.translation_string:
            return True
        return False

class Parser:
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
    def parse_file(cls, filename):
        fh = open(filename, "ru")
        return cls.parse(fh.read())

class StringSet:
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


    #def serialize(self):
        #d =  {
            #'filename' : self.filename,
            #'target_language' : self.target_language,
            #'strings' : [],
        #}
        #for i in self.strings:
            #d['strings'].append(i.serialize())
        #return d