# -*- coding: utf-8 -*-
"""
Handler for .desktop files.
"""

import re
import codecs
from collections import defaultdict
from transifex.txcommon.log import logger
from transifex.languages.models import Language
from transifex.resources.models import Translation, Template
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import Handler, StringSet, \
        GenericTranslation, ParseError, CompileError


class DesktopParseError(ParseError):
    pass


class DesktopCompileError(CompileError):
    pass


class DesktopHandler(Handler):
    """Class for .desktop files.

    See http://standards.freedesktop.org/desktop-entry-spec/latest/.
    """

    name = ".desktop file handler"
    mime_types = ['application/x-desktop']
    format = ".desktop (*.desktop)"
    comment_chars = ('#', )
    delimiter = '='
    # We are only intrested in localestrings, see
    # http://standards.freedesktop.org/desktop-entry-spec/latest/ar01s05.html
    localized_keys = ['Name', 'GenericName', 'Comment', 'Icon', ]

    @classmethod
    def accepts(cls, filename=None, mime=None):
        accept = False
        if filename is not None:
            accept |= filename.endswith(".desktop")
        if mime is not None:
            accept |= mime in cls.mime_types
        return accept

    @classmethod
    def contents_check(cls, filename):
        pass
        # fh = codecs.open(filename, "r", cls.default_encoding)
        # try:
        #     for line in fh:
        #         line = line.rstrip('\n')
        #         if self._should_skip(line):
        #             continue
        #         elif not '=' in line:
        #             raise DesktopParseError("Invalid line %s", line)
        # finally:
        #     fh.close()

    def _compile_translation(self, language, *args, **kwargs):
        """Compile a translation file."""
        stringset = self._get_strings(self.resource)
        for string in stringset:
            try:
                trans = Translation.objects.get(
                    source_entity__resource=self.resource, source_entity=string,
                    language=language, rule=5
                )
                translation_string = trans.string
            except Translation.DoesNotExist:
                trans = None
                translation_string = u""

            self.template = u''.join([
                    self.template,
                    string.string,
                    '[', language.code, ']=',
                    translation_string,
                    '\n',
            ])
        self.compiled_template = self.template

    def _compile_source(self, *args, **kwargs):
        """Compile a source file."""
        all_languages = set(self.resource.available_languages_without_teams)
        source_language = set([self.resource.source_language, ])
        translated_to = all_languages - source_language
        for language in translated_to:
            self._compile_translation(language)
        if not self.compiled_template:
            self.compiled_template = self.template

    def _is_comment_line(self, line):
        """Return True, if the line is a comment."""
        return line[0] in self.comment_chars

    def _is_empty_line(self, line):
        """Return True, if the line is empty."""
        return re.match('\s*$', line) is not None

    def _is_group_header_line(self, line):
        """Return True, if this is a group header."""
        return line[0] == '[' and line[-1] == ']'

    def _get_elements(self, line):
        """Get the key and the value of a line."""
        return line.split(self.delimiter, 1)

    def _get_lang_code(self, locale):
        """Return the lang_code part from a locale string.

        locale is of the form lang_COUNTRY.ENCODING@MODIFIER
        (in general)
        We care for lang_COUNTRY part.
        """
        modifier = ''
        at_pos = locale.find('@')
        if at_pos != -1:
            modifier = locale[at_pos:]
            locale = locale[:at_pos]
        dot_pos = locale.find('.')
        if dot_pos != -1:
            locale = locale[:dot_pos]
        return ''.join([locale, modifier])

    def _get_locale(self, key):
        """Get the locale part of a key."""
        return key[key.find('[') + 1:-1]

    def _should_skip(self, line):
        """Return True, if we should skip the line.

        This is the case if the line is an empty line, a comment or
        a group header line.

        """
        return self._is_empty_line(line) or\
                self._is_comment_line(line) or\
                self._is_group_header_line(line)

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parse a .desktop file.

        If it is a source file, the file will have every translation in it.
        Otherwise, it will have just the translation for the specific language.
        """
        stringset = StringSet()
        suggestions = StringSet()
        # entries is a dictionary with the entry keys in the file
        entries = defaultdict(list)

        fh = codecs.open(self.filename, "r", self.default_encoding)
        try:
            buf = fh.read()
        finally:
            fh.close()

        template = u''
        for line in buf.split("\n"):
            if self._should_skip(line) :
                template += line + "\n"
                continue
            key, value = self._get_elements(line)
            if '[' in key:
                # this is a translation
                # find the language of it
                # Skip the template
                actual_key = key[:key.find('[')]
                locale = self._get_locale(key)
                lang_code = self._get_lang_code(locale)
                if lang_code == "x-test":
                    template += line + "\n"
                    continue
                try:
                    lang = Language.objects.by_code_or_alias(lang_code)
                except Language.DoesNotExist, e:
                    msg = "Unknown language specified: %s" % lang_code
                    logger.warning(msg)
                    raise DesktopParseError(msg)
            else:
                lang = False    # Use False to mark source string
                actual_key = key
                template += line + "\n"

            if actual_key not in self.localized_keys:
                # Translate only standard localestring keys
                continue
            entries[actual_key].append((value, lang))

        context = ""
        template += '\n# Translations\n'

        for key, value in entries.iteritems():
            for translation, language in value:
                if is_source and language:
                    continue
                elif not is_source and language != self.language:
                    continue
                stringset.strings.append(GenericTranslation(
                        key, translation, rule=5, context=context,
                        pluralized=False, fuzzy=False, obsolete=False
                ))

        self.stringset = stringset
        self.suggestions = suggestions
        if is_source:
            self.template = template.encode(self.default_encoding)

    @need_resource
    def compile(self, language=None):
        if not language:
            language = self.language

        self._pre_compile(language=language)

        self.template = Template.objects.get(
            resource=self.resource
        ).content.decode(self.default_encoding)
        self._examine_content(self.template)

        if language == self.resource.source_language:
            self._compile_source(language)
        else:
            self._compile_translation(language)

        self.compiled_template = self.compiled_template.encode('UTF-8')
        self._post_compile(language)
