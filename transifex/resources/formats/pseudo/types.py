# -*- coding: utf-8 -*-
import re
from django.conf import settings
from transifex.resources.formats.pseudo import PseudoTypeMixin
from transifex.resources.formats.pseudo.splitters import *

class XxxPseudoType(PseudoTypeMixin):
    """Pseudo type for adding xxx around a string."""

    def _base_compile(self, string):
        return u'xxx' + string + u'xxx'

    def _po(self, string):
        """
        Custom pseudo method for PO based resources.
        
        Translations must begin and end with \n if the msgid does so.
        """
        return self._skip_char_around(string, char='\n')

    def _properties(self, string):
        """
        Custom pseudo method for PROPERTIES based resources.
        
        Translations with " (quote) around it should be kept like that.
        """
        #FIXME: It might not be really needed for java .properties files.
        # It was possible to find some .properties files that where using
        # KEY="string" structure, but apparently they were PHP based files.
        # In any case, lets keep it here until we be sure of its needed, once
        # it shouldn't affect the real Java .properties files.
        return self._skip_char_around(string, char='"')


#NOTE: Inherits custom methods from XxxPseudoType
class BracketsPseudoType(XxxPseudoType):
    """Pseudo type for adding square brackets around a string."""

    def _base_compile(self, string):
        return u'[' + string + u']'


class UnicodePseudoType(PseudoTypeMixin):
    """
    Pseudo type for converting all chars of a string into unicode chars that 
    look alike.
    """
    
    UNICODE_MAP = u"ȦƁƇḒḖƑƓĦĪĴĶĿḾȠǾƤɊŘŞŦŬṼẆẊẎẐ" + u"[\\]^_`" + \
        u"ȧƀƈḓḗƒɠħīĵķŀḿƞǿƥɋřşŧŭṽẇẋẏẑ"

    @classmethod
    def _transpose(cls, char):
        """Convert unicode char to something similar to it."""
        try:
            loc = ord(char)-65
            if loc < 0 or loc > 56:
                return char
            return cls.UNICODE_MAP[loc]
        except UnicodeDecodeError:
            return char

    @SplitterDecorators([TagSplitter, HTMLSpecialEntitiesSplitter, 
        PrintfSplitter, EscapedCharsSplitter])
    def _base_compile(self, string):
        return "".join(map(self._transpose, string))


class PLanguagePseudoType(PseudoTypeMixin):
    """
    Pseudo type for increasing the length of a string by around 30-50% 
    replacing the vowels with unicode chars that look alike.
    
    This pseudo type is based on a P-language, which is a simple 
    vowel-extending language. Examples:
    - "hello" becomes "héPéllôPô": hé + Pé + llô +Pô
    - "because" becomes "béPécåüPåüséPé": bé + Pé + cåü + Påü + sé + Pé
    
    Reference:
    http://src.chromium.org/viewvc/chrome/trunk/src/tools/grit/grit/pseudo.py
    """

    # Hebrew character Qof. It looks kind of like a 'p'.
    _QOF = u'\u05e7'   

    # How we map each vowel.
    _VOWELS = {
    u'a' : u'\u00e5',  # a with ring
    u'e' : u'\u00e9',  # e acute
    u'i' : u'\u00ef',  # i diaresis
    u'o' : u'\u00f4',  # o circumflex
    u'u' : u'\u00fc',  # u diaresis
    u'y' : u'\u00fd',  # y acute
    u'A' : u'\u00c5',  # A with ring
    u'E' : u'\u00c9',  # E acute
    u'I' : u'\u00cf',  # I diaresis
    u'O' : u'\u00d4',  # O circumflex
    u'U' : u'\u00dc',  # U diaresis
    u'Y' : u'\u00dd',  # Y acute
    }

    # Matches vowels and P
    _PSUB_RE = re.compile("(%s)" % '|'.join(_VOWELS.keys() + ['P']))

    @classmethod
    def Repl(cls, match):
        if match.group() == 'p':
            if also_p:
                return _QOF
            else:
                return 'p'
        else:
            return cls._VOWELS[match.group()]

    @classmethod
    def _MapVowels(cls, string, also_p=False):
        """
        Return a copy of ``string`` where characters that exist as keys in
        cls._VOWELS have been replaced with the corresponding value.  If 
        also_p is True, this function will also change capital P characters 
        into a Hebrew character Qof.
        """
        return cls._PSUB_RE.sub(cls.Repl, string)

    @SplitterDecorators([TagSplitter, HTMLSpecialEntitiesSplitter, 
        PrintfSplitter, EscapedCharsSplitter])
    def _base_compile(self, string):
        outstr = u''
        ix = 0
        while ix < len(string):
            if string[ix] not in self._VOWELS.keys():
                outstr += string[ix]
                ix += 1
            else:
                # We want to treat consecutive vowels as one composite vowel.
                consecutive_vowels = u''
                while ix < len(string) and string[ix] in self._VOWELS.keys():
                    consecutive_vowels += string[ix]
                    ix += 1
                changed_vowels = self._MapVowels(consecutive_vowels)
                outstr += changed_vowels
                outstr += self._QOF
                outstr += changed_vowels
        return outstr
