# -*- coding: utf-8 -*-

"""
Java properties file handler/compiler
"""
import os, re
import codecs
from django.utils.hashcompat import md5_constructor

from transifex.txcommon.log import logger
from transifex.resources.formats.utils.decorators import *

from core import GenericTranslation, Handler, STRICT, \
    StringSet
from transifex.resources.models import SourceEntity

class JavaPropertiesHandler(Handler):
    """
    Handler for Java PROPERTIES translation files.
    """
    name = "Java *.PROPERTIES file handler"
    mime_types = []
    format = "Java PROPERTIES (*.properties)"
    @classmethod
    def accept(cls, filename=None, mime=None):
        return filename.endswith(".properties") or mime in cls.mime_types

    @classmethod
    def contents_check(self, filename):
        pass
        
    def __str__(self):
        s='{'
        for key,value in self._props.items():
            s = ''.join((s,key,'=',value,', '))

        s=''.join((s[:-2],'}'))
        return s

    def __parse(self, lines):
        """ Parse a list of lines and create
        an internal property dictionary """

        # Every line in the file must consist of either a comment
        # or a key-value pair. A key-value pair is a line consisting
        # of a key which is a combination of non-white space characters
        # The separator character between key-value pairs is a '=',
        # ':' or a whitespace character not including the newline.
        # If the '=' or ':' characters are found, in the line, even
        # keys containing whitespace chars are allowed.

        # A line with only a key according to the rules above is also
        # fine. In such case, the value is considered as the empty string.
        # In order to include characters '=' or ':' in a key or value,
        # they have to be properly escaped using the backslash character.

        # Some examples of valid key-value pairs:
        #
        # key     value
        # key=value
        # key:value
        # key     value1,value2,value3
        # key     value1,value2,value3 \
        #         value4, value5
        # key
        # This key= this value
        # key = value1 value2 value3
        
        # Any line that starts with a '#' or '!' is considerered a comment
        # and skipped. Also any trailing or preceding whitespaces
        # are removed from the key/value.
        
        # This is a line parser. It parses the
        # contents like by line.

        lineno=0
        i = iter(lines)

        for line in i:
            lineno += 1
            line = line.strip()
            # Skip null lines
            if not line: continue
            # Skip lines which are comments
            if line[0] in ('#','!'): continue
            # Some flags
            escaped=False
            # Position of first separation char
            sepidx = -1
            # A flag for performing wspace re check
            flag = 0
            # Check for valid space separation
            # First obtain the max index to which we
            # can search.
            m = self.othercharre.search(line)
            if m:
                first, last = m.span()
                start, end = 0, first
                flag = 1
                wspacere = re.compile(r'(?<![\\\=\:])(\s)')        
            else:
                if self.othercharre2.search(line):
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
                logger.debug('Space match=>'+line)
                # Means we need to split by space.
                first, last = m2.span()
                sepidx = first
            elif m:
                logger.debug('Other match=>'+line)
                # No matching wspace char found, need
                # to split by either '=' or ':'
                first, last = m.span()
                sepidx = last - 1
                logger.debug(line[sepidx])
                
                
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
                key,value = line,''
            self._keyorder.append(key)
            self.processPair(key, value)
            
    def processPair(self, key, value):
        """ Process a (key, value) pair """

        oldkey = key
        oldvalue = value
        
        # Create key intelligently
        keyparts = self.bspacere.split(key)
        #logger.debug(keyparts)

        strippable = False
        lastpart = keyparts[-1]

        if lastpart.find('\\ ') != -1:
            keyparts[-1] = lastpart.replace('\\','')

        # If no backspace is found at the end, but empty
        # space is found, strip it
        elif lastpart and lastpart[-1] == ' ':
            strippable = True

        key = ''.join(keyparts)
        if strippable:
            key = key.strip()
            oldkey = oldkey.strip()
        
        oldvalue = self.unescape(oldvalue)
        value = self.unescape(value)

        # Patch from N B @ ActiveState
        curlies = re.compile("{.+?}")
        found = curlies.findall(value)

        for f in found:
            srcKey = f[1:-1]
            if self._props.has_key(srcKey):
                value = value.replace(f, self._props[srcKey], 1)

        self._props[key] = value.strip()

        # Check if an entry exists in pristine keys
        if self._keymap.has_key(key):
            oldkey = self._keymap.get(key)
            self._origprops[oldkey] = oldvalue.strip()
        else:
            self._origprops[oldkey] = oldvalue.strip()
            # Store entry in keymap
            self._keymap[key] = oldkey
        
        if key not in self._keyorder:
            self._keyorder.append(key)
        
    def escape(self, value):

        # Java escapes the '=' and ':' in the value
        # string with backslashes in the store method.
        # So let us do the same.
        newvalue = value.replace(':','\:')
        newvalue = newvalue.replace('=','\=')

        return newvalue

    def unescape(self, value):

        # Reverse of escape
        newvalue = value.replace('\:',':')
        newvalue = newvalue.replace('\=','=')

        return newvalue    
        
    def load(self, stream):
        """ Load properties from an open file stream """
        self._props = {}
        self._origprops = {}
        self._keyorder = []
        self._keymap = {}
        
        self.othercharre = re.compile(r'(?<!\\)(\s*\=)|(?<!\\)(\s*\:)')
        self.othercharre2 = re.compile(r'(\s*\=)|(\s*\:)')
        self.bspacere = re.compile(r'\\(?!\s$)')

        lines = stream.split('\n')
        if lines[-1] == '':
            lines.pop()
        for line in lines:
            lines[lines.index(line)] = line + '\n'
        self.__parse(lines)


    def getPropertyDict(self):
        return self._props


    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parse a PROPERTIES file and create a stringset with all entries in the file.
        """
        resource = self.resource
        stringset = StringSet()
        suggestions = StringSet()

        fh = codecs.open(self.filename, "r", "utf-8")

        buf = fh.read()
        fh.close()
        self.load(buf)
        propertyDict = self.getPropertyDict()
        for property in propertyDict:
            source = property
            trans = propertyDict[property]
            line = (source + '=' + trans)#.decode('utf-8')
            # We use empty context
            context = ""

            if is_source:
                if trans.strip()!="":
                    new_line = re.sub(re.escape(trans), "%(hash)s_tr" % {'hash':md5_constructor(
                        ':'.join([source,context]).encode('utf-8')).hexdigest()}, line)
    
                    # this looks fishy
                    buf = re.sub(re.escape(line), new_line, buf)
                else:
                    continue
            else:
                try:
                    if SourceEntity.objects.get(resource=resource, string=source) and trans.strip()!="":
                        pass
                    else:
                        continue
                except:
                    continue
                    
            stringset.strings.append(GenericTranslation(source,
                trans, rule=5, context=context,
                pluralized=False, fuzzy=False,
                obsolete=False))

        self.stringset=stringset
        self.suggestions=suggestions

        if is_source:
            self.template = str(buf.encode('utf-8'))
