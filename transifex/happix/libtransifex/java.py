# -*- coding: utf-8 -*-
"""
Java .properties file parser
"""
import os, re
from core import StringSet, Parser, Translation, CompileError, ParseError

class PropsParseError(ParseError):
    pass

class PropsCompileError(CompileError):
    pass

class JavaPropertiesParser(Parser):
    """
    Java Properties are described here:
    http://java.sun.com/j2se/1.4.2/docs/api/java/util/Properties.html
    """
    name = "Java .properties parser"
    format = "Java Resource Bundles (*.properties)"
    mime_type = "text/java-properties" # Not official
    default_encoding = "iso-8859-1" # Used for reading/saving files

    @classmethod
    def accept(cls, filename):
        return filename.endswith(".properties")

    @classmethod
    def compile(cls, stringset):
        def prop_escape(j):
            """
            Escape Unicode string:
            * encode in 'unicode_escape' to replace special chars with \xFF notation
            * replace \xFF notation with \u00FF notation
            * replace \\ with \u005c which stands for \ in Unicode
            """
            return j.encode('unicode_escape').replace("\\x", "\\u00").replace("\\\\", "\\u005c")

        buf = u""
        for i in stringset.strings:
            buf += u"%s=%s\n" % (i.source_entity, prop_escape(i.translation_string))
        return buf
        
    @classmethod
    def parse(cls, buf):
        """
        Parsing implementation from:
        http://code.activestate.com/recipes/496795-a-python-replacement-for-javautilproperties/
        """
        stringset = StringSet()

        othercharre = re.compile(r'(?<!\\)(\s*\=)|(?<!\\)(\s*\:)')
        othercharre2 = re.compile(r'(\s*\=)|(\s*\:)')

        lineno=0
        i = iter(buf.split("\n"))
        stringset.strings = []
        for line in i:
            lineno += 1
#            line = line.strip()
            # Skip null lines
            if not line: continue
            # Skip lines which are comments
            if line[0] == '#': continue
            # Some flags
            escaped=False
            # Position of first separation char
            sepidx = -1
            # A flag for performing wspace re check
            flag = 0
            # Check for valid space separation
            # First obtain the max index to which we
            # can search.
            m = othercharre.search(line)
            if m:
                first, last = m.span()
                start, end = 0, first
                flag = 1
                wspacere = re.compile(r'(?<![\\\=\:])(\s)')        
            else:
                if othercharre2.search(line):
                    # Check if either '=' or ':' is present
                    # in the line. If they are then it means
                    # they are preceded by a backslash.
                    
                    # This means, we need to modify the
                    # wspacere a bit, not to look for
                    # : or = characters.
                    wspacere = re.compile(r'(?<![\\])(\s)')        
                start, end = 0, len(line)
                
            m2 = wspacere.search(line, start, end)
            if m2:
                # print 'Space match=>',line
                # Means we need to split by space.
                first, last = m2.span()
                sepidx = first
            elif m:
                # print 'Other match=>',line
                # No matching wspace char found, need
                # to split by either '=' or ':'
                first, last = m.span()
                sepidx = last - 1
                # print line[sepidx]
                
                
            # If the last character is a backslash
            # it has to be preceded by a space in which
            # case the next line is read as part of the
            # same property
            while line[-1] == '\\':
                # Read next line
                nextline = i.next()
                nextline = nextline.strip()
                lineno += 1
                # This line will become part of the value
                line = line[:-1] + nextline

            # Now split to key,value according to separation char
            if sepidx != -1:
                key, value = line[:sepidx], line[sepidx+1:]
            else:
                key, value = line, ''
            if "\\u" in value:
                value = value.decode('unicode_escape')
            stringset.strings.append(Translation(key, value))
        return stringset
