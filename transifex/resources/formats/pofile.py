# -*- coding: utf-8 -*-

"""
GNU Gettext .PO/.POT file handler/compiler
"""
import os, re, time
import polib, datetime
from django.conf import settings
from django.db import transaction
from django.db.models import get_model
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.hashcompat import md5_constructor

from transifex.txcommon.commands import run_command, CommandError
from transifex.txcommon.exceptions import FileCheckError
from transifex.txcommon.log import logger
from transifex.teams.models import Team
from transifex.resources.formats.decorators import *
from transifex.resources.stats import ResourceStatsList
from suggestions.models import Suggestion

from core import CompileError, GenericTranslation, Handler, STRICT, \
    StringSet, ParseError

#class ResXmlParseError(ParseError):
    #pass

#class ResXmlCompileError(CompileError):
    #pass

Resource = get_model('resources', 'Resource')
Translation = get_model('resources', 'Translation')
SourceEntity = get_model('resources', 'SourceEntity')
Storage = get_model('storage', 'StorageFile')

def escape(st):
    """
    Escape special chars and return the given string *st*.

    **Examples**:

    >>> escape('\\t and \\n and \\r and " and \\\\')
    '\\\\t and \\\\n and \\\\r and \\\\" and \\\\\\\\'
    """
    return st.replace('\\', r'\\\\')\
             .replace('\n', r'\\n')\
             .replace('\t', r'\\t')\
             .replace('\r', r'\\r')\
             .replace('\"', r'\\"')

def get_po_contents(pofile):
    """
    This function takes a pofile object and returns its contents
    """

    # FIXME: Temporary check until a version greater than polib-0.5.3 is out.
    # Patch sent to upstream.
    def charset_exists(charset):
        """Check whether or not ``charset`` is valid."""
        import codecs
        try:
            codecs.lookup(charset)
        except LookupError:
            return False
        return True

    if not charset_exists(pofile.encoding):
        pofile.encoding = polib.default_encoding

    return pofile.__str__()

def msgfmt_check(po_contents, ispot=False, with_exceptions=True):
    """
    Run a `msgfmt -c` on the file contents.

    Raise a FileCheckError in case the stderror has errors/warnings or
    the command execution returns Error.
    """
    try:
        if ispot:
            command = 'msgfmt -o /dev/null --check-format --check-domain -'
        else:
            command = 'msgfmt -o /dev/null -c -'
        status, stdout, stderr = run_command(command, _input=po_contents,
            with_extended_output=True, with_exceptions=with_exceptions)
        # Not sure why msgfmt sends its output to stderr instead of stdout
        #if 'warning:' in stderr or 'too many errors, aborting' in stderr:
        if 'too many errors, aborting' in stderr:
            raise CommandError(command, status, stderr)
    except CommandError:
        logger.debug("pofile: The 'msgfmt -c' check failed.")
        raise FileCheckError, ugettext("Your file failed a correctness check "
            "(msgfmt -c). Please run this command on "
            "your system to see the errors.")


class POHandler(Handler):
    """
    Translate Toolkit is using Gettext C library to parse/create PO files in Python
    TODO: Switch to Gettext C library
    """
    name = "GNU Gettext *.PO/*.POT handler"
    mime_types = ["application/x-gettext", "application/x-po", "text/x-po"]
    format = "GNU Gettext Catalog (*.po, *.pot)"

    @classmethod
    def accept(cls, filename=None, mime=None):
        return filename.endswith(".po") or filename.endswith(".pot") or\
            mime in cls.mime_types

    @classmethod
    def contents_check(self, filename):

        # Read the stream to buffer
        po = polib.pofile(filename)

        # get this back once the polib bug has been fixed :
        # http://bitbucket.org/izi/polib/issue/11/multiline-entries-are-not-getting-updated
        #buf = get_po_contents(po)

        # Temporary solution
        buf = open(filename, 'r').read()

        # If file is empty, the method hangs so we should bail out.
        if not buf:
            logger.error("pofile: File '%s' is empty." % filename)
            raise FileCheckError("Uploaded file is empty.")

        # Msgfmt check
        if settings.FILECHECKS['POFILE_MSGFMT']:
            if filename.lower().endswith('.pot'):
                ispot = True
            else:
                ispot = False
            msgfmt_check(buf, ispot)

        # Check required header fields 
        required_metadata = ['Content-Type', 'Content-Transfer-Encoding']
        for metadata in required_metadata:
            if not metadata in po.metadata:
                logger.debug("pofile: Required metadata '%s' not found." % 
                    metadata)
                raise FileCheckError("Uploaded file header doesn't "
                "have '%s' metadata!" % metadata)


        # No translated entries check
#        if len(po.translated_entries()) + len(po.fuzzy_entries()) < 1:
#            logger.debug("pofile: No translations found!")
#            raise FileCheckError(_("Uploaded file doesn't contain any "
#                "translated entries!"))
#

    def _do_replace(self, original, replacement, text):
        """
        It just does a search and replace inside `text` and replaces all
        occurrences of `original` with `replacement`. For pofiles we also want
        to escape all special characters
        """
        return re.sub(re.escape(original), escape(replacement), text)


    @need_compiled
    def _post_compile(self, *args, **kwargs):
        """
        Here we update the PO file headers and the plurals
        """
        if hasattr(kwargs,'language'):
            language = kwargs['language']
        else:
            language = self.language

        template = self.compiled_template
        po = polib.pofile(template)

        # Update PO file headers
        po.metadata['Project-Id-Version'] = self.resource.project.name.encode("utf-8")
        po.metadata['Content-Type'] = "text/plain; charset=UTF-8"
        po.metadata['PO-Revision-Date'] = (datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M+0000").encode("utf-8"))
        po.metadata['Plural-Forms'] = ("nplurals=%s; plural=%s" % (language.nplurals, language.pluralequation)).encode("utf-8")
        # The following is in the specification but isn't being used by po
        # files. What should we do?
        po.metadata['Language'] = (language.code.encode("utf-8"))

        if self.resource.project.bug_tracker:
            po.metadata['Report-Msgid-Bugs-To'] = (self.resource.project.bug_tracker.encode("utf-8"))

        if 'fuzzy' in po.metadata_is_fuzzy:
            po.metadata_is_fuzzy.remove('fuzzy')

        try:
            team = Team.objects.get(language = language,
                project = self.resource.project.outsource or self.resource.project)
        except Team.DoesNotExist:
            pass
        else:
            po.metadata['Language-Team'] = ("%s <%s>" % (language.name ,
                team.mainlist)).encode("utf-8")

        stat = ResourceStatsList(self.resource).stat(language)
        if stat.last_committer:
            u = stat.last_committer
            po.metadata['Last-Translator'] = ("%s <%s>" %
                (u.get_full_name() or u.username , u.email)).encode("utf-8")

        for entry in po:
            if entry.msgid_plural:
                plurals = Translation.objects.filter(
                    source_entity__resource = self.resource,
                    language = language,
                    source_entity__string = entry.msgid)
                plural_keys = {}
                # last rule excluding other(5)
                lang_rules = language.get_pluralrules_numbers()
                # Initialize all plural rules up to the last
                for p,n in enumerate(lang_rules):
                    plural_keys[p] = ""
                for n,p in enumerate(plurals):
                    plural_keys[n] =  p.string

                entry.msgstr_plural = plural_keys

        # Instead of saving raw text, we save the polib Handler
        self.compiled_template = get_po_contents(po)
        return po

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parse a PO file and create a stringset with all PO entries in the file.
        """
        stringset = StringSet()
        suggestions = StringSet()
        # For .pot files the msgid entry must be used as the translation for
        # the related language.
        if self.filename.endswith(".pot") or is_source:
            ispot = True
        else:
            ispot = False

        if lang_rules:
            nplural = len(lang_rules)
        else:
            nplural = self.language.get_pluralrules_numbers()

        pofile = polib.pofile(self.filename)

        for entry in pofile:
            pluralized = False
            same_nplural = True

            # treat fuzzy translation as nonexistent
            if "fuzzy" in entry.flags:
                if not ispot:
                    if not entry.msgid_plural:
                        suggestion = GenericTranslation(entry.msgid, entry.msgstr,
                            context=entry.msgctxt or '',
                            occurrences=', '.join(
                                [':'.join([i for i in t ]) for t in
                                entry.occurrences]))
                        suggestions.strings.append(suggestion)

                    continue
                else:
                    # Drop fuzzy flag from template
                    entry.flags.remove("fuzzy")



            if entry.msgid_plural:
                pluralized = True
                if ispot:
                    # English plural rules
                    messages = [(1, entry.msgid),
                                (5, entry.msgid_plural)]
                    plural_keys = [0,1]
                else:
                    message_keys = entry.msgstr_plural.keys()
                    message_keys.sort()
                    nplural_file = len(message_keys)
                    messages = []
                    if nplural:
                        if len(nplural) != nplural_file:
                            logger.error("Passed plural rules has nplurals=%s"
                                ", but '%s' file has nplurals=%s. String '%s'"
                                "skipped." % (nplural, self.filename, nplural_file,
                                entry.msgid))
                            same_nplural = False
                    else:
                        same_nplural = False

                    if not same_nplural:
                        # Skip half translated plurals
                        continue
                        # plural_keys = message_keys

                    for n, key in enumerate(message_keys):
                        messages.append((nplural[n], entry.msgstr_plural['%s' % n]))
            else:
                # pass empty strings for non source files
                if not ispot and entry.msgstr in ["", None]:
                    continue
                # Not pluralized, so no plural rules. Use 5 as 'other'.
                if ispot:
                    messages = [(5, entry.msgid)]
                else:
                    messages = [(5, entry.msgstr)]

            # Add messages with the correct number (plural)
            for number, msgstr in enumerate(messages):
                translation = GenericTranslation(entry.msgid, msgstr[1],
                    context=entry.msgctxt or '',
                    occurrences=', '.join(
                        [':'.join([i for i in t ]) for t in entry.occurrences]),
                    rule=msgstr[0], pluralized=pluralized)

                stringset.strings.append(translation)

            if entry.comment:
                translation.comment = entry.comment
            if entry.flags:
                translation.flags = ', '.join( f for f in entry.flags)

            if is_source:
                entry.msgstr = "%(hash)s_tr" % {'hash':
                    md5_constructor(':'.join([translation.source_entity,
                    translation.context]).encode('utf-8')).hexdigest()}

                if entry.msgid_plural:
                    for n, rule in enumerate(plural_keys):
                        entry.msgstr_plural['%s' % n] = ("%(hash)s_pl_%(key)s" %
                            {'hash':md5_constructor(':'.join([translation.source_entity,
                            translation.context]).encode('utf-8')).hexdigest(), 'key':n})


        if is_source:
            self.template =  get_po_contents(pofile)

        self.stringset = stringset
        self.suggestions = suggestions
        return pofile

    @need_compiled
    def save2file(self, filename):
        """
        Take the ouput of the compile method and save results to specified
        file. To avoid an extra step here, we take the polib.pofile handler and
        save directly to the file.
        """
        try:
            self.compiled_template.save(filename)
        except Exception, e:
            raise Exception("Error opening file %s: %s" % ( filename, e))
