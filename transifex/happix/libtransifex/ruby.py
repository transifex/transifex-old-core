# -*- coding: utf-8 -*-

import os
from syck import load as parse_yaml
from core import StringSet, ParseError, Parser

class YamlParseError(ParseError):
    pass

class YamlParser(Parser):
    name = "Ruby On Rails .yml parser"
    @classmethod
    def accept(cls, filename):
        return filename[-4:].lower() == ".yml" #and \
            #os.path.basename(os.path.dirname(filename)).lower() == "locales"
            

    @classmethod
    def parse(cls, buf):
        pass

    @classmethod
    def compile(cls, stringset):
        pass