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

from django.contrib.sites.models import Site

from transifex.txcommon.commands import run_command, CommandError
from transifex.txcommon.exceptions import FileCheckError
from transifex.txcommon.log import logger
from transifex.teams.models import Team
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.models import RLStats
from transifex.resources.signals import post_save_translation
from suggestions.models import Suggestion

from transifex.resources.formats.core import CompileError, GenericTranslation, \
        Handler, STRICT, StringSet, ParseError

#class ResXmlParseError(ParseError):
    #pass

#class ResXmlCompileError(CompileError):
    #pass

Resource = get_model('resources', 'Resource')
Translation = get_model('resources', 'Translation')
SourceEntity = get_model('resources', 'SourceEntity')
Template = get_model('resources', 'Template')
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
    copyright_line = re.compile('^# (.*?), ((\d{4}(, ?)?)+)\.?$')

    @classmethod
    def accepts(cls, filename=None, mime=None):
        accept = False
        if filename is not None:
            accept |= filename.endswith(".po") or filename.endswith(".pot")
        if mime is not None:
            accept |= mime in cls.mime_types
        return accept

    @classmethod
    def contents_check(self, filename):

        # Read the stream to buffer
        po = polib.pofile(filename)

        # get this back once the polib bug has been fixed :
        # http://bitbucket.org/izi/polib/issue/11/multiline-entries-are-not-getting-updated
        #buf = self.get_po_contents(po)

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

    def __init__(self, filename=None, resource= None, language = None):
        super(POHandler, self).__init__(filename, resource, language)
        self.copyrights = []

    def get_po_contents(self, pofile):
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

        content = pofile.__str__()
        stripped_content = ""
        for line in content.split('\n'):
            if not self._is_copyright_line(line):
                stripped_content += line + "\n"
        return stripped_content

    def _do_replace(self, original, replacement, text):
        """
        It just does a search and replace inside `text` and replaces all
        occurrences of `original` with `replacement`. For pofiles we also want
        to escape all special characters
        """
        return re.sub(re.escape(original), escape(replacement), text)

    @need_resource
    def compile_pot(self):
        template = Template.objects.get(resource=self.resource)
        template = template.content
        self._peek_into_template()

        stringset = SourceEntity.objects.filter(
            resource = self.resource)

        for string in stringset:
            # Replace strings with ""
            template = self._do_replace(
                "%s_tr" % string.string_hash.encode('utf-8'), "", template
            )

        # FIXME merge with _post_compile
        po = polib.pofile(unicode(template, 'utf-8'))

        # Update PO file headers
        po.metadata['Project-Id-Version'] = self.resource.project.name.encode("utf-8")
        po.metadata['Content-Type'] = "text/plain; charset=UTF-8"
        # The above doesn't change the charset of the actual object, so we
        # need to do it for the pofile object as well.
        po.encoding = "UTF-8"

        if self.resource.project.bug_tracker:
            po.metadata['Report-Msgid-Bugs-To'] = (self.resource.project.bug_tracker.encode("utf-8"))

        for entry in po:
            if entry.msgid_plural:
                plurals = Translation.objects.filter(
                    source_entity__resource = self.resource,
                    language = self.resource.source_language,
                    source_entity__string = entry.msgid
                ).order_by('rule')
                plural_keys = {}
                # last rule excluding other(5)
                lang_rules = self.resource.source_language.get_pluralrules_numbers()
                # Initialize all plural rules up to the last
                for p,n in enumerate(lang_rules):
                    plural_keys[p] = ""
                for n,p in enumerate(plurals):
                    plural_keys[n] =  ""

                entry.msgstr_plural = plural_keys
        self.compiled_template = self.get_po_contents(po)

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
        po = polib.pofile(unicode(template, 'utf-8'))

        # Update PO file headers
        po.metadata['Project-Id-Version'] = self.resource.project.name.encode("utf-8")
        po.metadata['Content-Type'] = "text/plain; charset=UTF-8"
        # The above doesn't change the charset of the actual object, so we
        # need to do it for the pofile object as well.
        po.encoding = "UTF-8"

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
            team_contact = "<%s>" % team.mainlist if team.mainlist else \
                "(http://%s%s)" % (Site.objects.get_current().domain,
                                   team.get_absolute_url())

            po.metadata['Language-Team'] = "%s %s" % (language.name,
                                                      team_contact)

        stat = RLStats.objects.by_resource(self.resource).by_language(language)
        if stat and stat[0].last_committer:
            u = stat[0].last_committer
            po.metadata['Last-Translator'] = ("%s <%s>" %
                (u.get_full_name() or u.username , u.email)).encode("utf-8")
            po.metadata['PO-Revision-Date'] = ( stat[0].last_update.strftime(
                "%Y-%m-%d %H:%M+0000").encode("utf-8") )

        for entry in po:
            if entry.msgid_plural:
                plurals = Translation.objects.filter(
                    source_entity__resource = self.resource,
                    language = language,
                    source_entity__string = entry.msgid
                ).order_by('rule')
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
        self.compiled_template = self.get_po_contents(po)

        # Add copyright headers if any
        from transifex.addons.copyright.models import Copyright
        c = Copyright.objects.filter(
            resource=self.resource, language=self.language
        )
        content_with_copyright = ""
        copyrights_inserted = False
        for line in self.compiled_template.split('\n'):
            if line.startswith('#'):
                content_with_copyright += line + "\n"
            elif not copyrights_inserted:
                copyrights_inserted = True
                for entry in c:
                    content_with_copyright += '# ' + entry.owner.encode('UTF-8') + \
                            ', ' + entry.years_text.encode('UTF-8') + "\n"
            else:
                content_with_copyright += line + "\n"
        self.compiled_template = content_with_copyright
        return po

    def _post_save2db(self, *args, **kwargs):
        """Emit a signal for others to catch."""
        post_save_translation.send(
            sender=self, resource=self.resource,
            language=self.language, copyrights=self.copyrights
        )

    @need_language
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parse a PO file and create a stringset with all PO entries in the file.
        """
        stringset = StringSet()
        suggestions = StringSet()

        if lang_rules:
            nplural = len(lang_rules)
        else:
            nplural = self.language.get_pluralrules_numbers()

        self._parse_copyrights(self.filename)
        pofile = polib.pofile(self.filename)

        for entry in pofile:
            pluralized = False
            same_nplural = True

            # skip obsolete entries
            if entry.obsolete:
                continue

            # treat fuzzy translation as nonexistent
            if "fuzzy" in entry.flags:
                if not is_source:
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
                if is_source:
                    nplural_file = len(entry.msgstr_plural.keys())
                    if nplural_file != 2:
                        raise FileCheckError("Your source file is not a POT file and"
                            " the translation file you're using has more"
                            " than two plurals which is not supported.")
                    # English plural rules
                    messages = [(1, entry.msgstr_plural['0'] or entry.msgid),
                                (5, entry.msgstr_plural['1'] or entry.msgid_plural)]
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
                if not is_source and entry.msgstr in ["", None]:
                    continue
                # Not pluralized, so no plural rules. Use 5 as 'other'.
                if is_source:
                    messages = [(5, entry.msgstr or entry.msgid)]
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
                entry.msgstr = "%(hash)s_tr" % {
                    'hash': hash_tag(translation.source_entity, translation.context)
                }

                if entry.msgid_plural:
                    for n, rule in enumerate(plural_keys):
                        entry.msgstr_plural['%s' % n] = (
                            "%(hash)s_pl_%(key)s" % {
                                'hash':hash_tag(translation.source_entity, translation.context),
                                'key':n
                            }
                        )

        if is_source:
            self.template =  self.get_po_contents(pofile)

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

    def _parse_copyrights(self, filename):
        """
        Read the copyrights (if any) from a po file.
        """
        # TODO remove FIRST AUTHOR line
        if filename.endswith('pot'):
            return
        f = open(filename)
        try:
            for line in f:
                if not line.startswith('#'):
                    break
                c = self._get_copyright_from_line(line)
                if c is not None:
                    self.copyrights.append(c)
        finally:
            f.close()

    def _get_copyright_from_line(self, line):
        """
        Get the copyright info from the line.

        Returns (owner, year) or None.
        """
        m = self.copyright_line.search(line)
        if m is None:
            return None
        owner = m.group(1)
        years = [y.strip() for y in m.group(2).split(',')]
        return (owner, years)

    def _is_copyright_line(self, line):
        return self.copyright_line.search(line) is not None

    def _get_copyright_lines():
        pass
