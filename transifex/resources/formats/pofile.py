# -*- coding: utf-8 -*-

"""
GNU Gettext .PO/.POT file handler/compiler
"""
import os, re, time, uuid
from hashlib import md5
import polib, datetime
from django.conf import settings
from django.db import transaction
from django.db.models import get_model
from django.utils.translation import ugettext, ugettext_lazy as _
from core import (CompileError, GenericTranslation, Handler, STRICT, StringSet,
                  ParseError, escape)

from txcommon.commands import run_command, CommandError
from txcommon.exceptions import FileCheckError
from txcommon.log import logger
from teams.models import Team

from resources.formats.decorators import *

#class ResXmlParseError(ParseError):
    #pass

#class ResXmlCompileError(CompileError):
    #pass
Resource = get_model('resources', 'Resource')
Translation = get_model('resources', 'Translation')
SourceEntity = get_model('resources', 'SourceEntity')
Storage = get_model('storage', 'StorageFile')


def get_po_contents(pofile):
    """
    This function takes a pofile object and returns it's contents
    """
    #FIXME: The following line could fix the issue. Test it.
    #return pofile.__str__()

    filename = time.time()
    pofile.save("/tmp/%s.tmp" % filename)
    file = open("/tmp/%s.tmp" % filename, 'r')
    file.seek(0)
    content = file.read()
    os.unlink("/tmp/%s.tmp" % filename)

    return content


def msgfmt_check(po_contents, with_exceptions=True):
    """
    Run a `msgfmt -c` on the file contents.

    Raise a FileCheckError in case the stderror has errors/warnings or
    the command execution returns Error.
    """
    try:
        command = 'msgfmt -o /dev/null -c -'
        status, stdout, stderr = run_command(command, _input=po_contents,
            with_extended_output=True, with_exceptions=with_exceptions)
        # Not sure why msgfmt sends its output to stderr instead of stdout
        if 'warning:' in stderr or 'too many errors, aborting' in stderr:
            raise CommandError(command, status, stderr)
    except CommandError:
        logger.debug("pofile: The 'msgfmt -c' check failed.")
        raise FileCheckError, ugettext("Your file does not pass by the check "
            "for correctness (msgfmt -c). Please run this command on "
            "your system to see the errors.")


class POHandler(Handler):
    """
    Translate Toolkit is using Gettext C library to parse/create PO files in Python
    TODO: Switch to Gettext C library
    """
    name = "GNU Gettext *.PO/*.POT handler"
    mime_type = "application/x-gettext"
    format = "GNU Gettext Catalog (*.po, *.pot)"

    @classmethod
    def accept(cls, filename):
        return filename.endswith(".po") or filename.endswith(".pot")

    @classmethod
    def contents_check(self, filename):

        # Read the stream to buffer
        po = polib.pofile(filename)
        buf = get_po_contents(po)

        # Msgfmt check
        if settings.FILECHECKS['POFILE_MSGFMT']:
            msgfmt_check(buf)

        # Check wether file containts DOS newlines '\r' (0x0D)
        # To remove you can run: tr -d '\r' < inputfile > outputfile
        if settings.FILECHECKS.get('DOS_NEWLINES', None):
            if '\r' in buf:
                logger.debug("pofile: DOS newlines (\\r) found!")
                raise FileCheckError(_("Uploaded file contains "
                    "DOS newlines (\\r)!"))

        # Check required header fields 
        required_metadata = ['Content-Type', 'Content-Transfer-Encoding']
        for metadata in required_metadata:
            if not metadata in po.metadata:
                logger.debug("pofile: Required metadata '%s' not found." % 
                    metadata)
                raise FileCheckError(_("Uploaded file header doesn't "
                "have '%s' metadata!") % metadata)

        # Check charset in header (UTF-8)
        if settings.FILECHECKS['UTF8']:
            if not "charset=utf-8" in po.metadata["Content-Type"].lower():
                logger.debug("pofile: Only UTF-8 encoded files are allowed!")
                raise FileCheckError(_("Only UTF-8 encoded files are allowed!"))

        # No translated entires check
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
        return re.sub(original, escape(replacement), text)


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

        # save to a temp dir to load in polib
        filename = time.time()
        file = open("/tmp/%s.tmp" % filename, 'w')
        file.write(template)
        file.flush()
        po = polib.pofile("/tmp/%s.tmp" % filename)
        os.unlink("/tmp/%s.tmp" % filename)

        # Update POFile Headers
        po.metadata['PO-Revision-Date'] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M+0000")
        po.metadata['Plural-Forms'] = "nplurals=%s; plural=%s" % (language.nplurals, language.pluralequation)
        # The following is in the specification but it's not being used by po
        # files. What should we do?
        po.metadata['Language'] = language.code

        try:
            team = Team.objects.get(language = language,
                project = self.resource.project)
        except Team.DoesNotExist:
            pass
        else:
            po.metadata['Language-Team'] = ("%s <%s>" % (language.name %
                team.mainlist))
        if self.resource.last_committer:
            u = self.resource.last_committer
            po.metadata['Last-Translator'] = ("%s <%s>" %
                (u.get_full_name() or u.username , u.email))

        for entry in po:
            if entry.msgid_plural:
                plurals = Translation.objects.filter(
                    resource = self.resource,
                    language = language,
                    source_entity__string = entry.msgid)
                plural_keys = {}
                # last rule excluding other(5)
                last_rule = language.get_pluralrules_numbers()[-2]
                # Initialize all plural rules up to the last
                for p in range(0,last_rule):
                    plural_keys[p] = ""
                for n,p in enumerate(plurals):
                    plural_keys[n] =  p.string

                entry.msgstr_plural = plural_keys

        # Instead of saving raw text, we save the polib Handler
        self.compiled_template = get_po_contents(po)
        return po

#    @need_resource
#    def compile(self, language = None):
#        #XXX: OBSOLETE
#        """
#        Compile a resource's strings into a PO file.
#        """
#        if not language:
#            language = self.language
#        # Create POFile
#        po = polib.POFile()
#
#        # Update POFile Headers
#        self.metadata['PO-Revision-Date'] = datetime.datetime.utcnow().strftime("%d-%m-%Y %H:%M+0000")
#        # The followin is in the specification but it's not being used by po
#        # files. What should we do?
#        self.metadata['Language'] = language.code
#        self.metadata['Plural-Forms'] = language.pluralequation
#
#        try:
#            team = Team.objects.get(language = language,
#                project = self.resource.project)
#        except Team.DoesNotExist:
#            pass
#        else:
#            self.metadata['Language-Team'] = ("%s <%s>" % (language.name %
#                team.mainlist))
#        if self.resource.last_committer:
#            u = self.resource.last_committer
#            self.metadata['Last-Translator'] = ("%s <%s>" %
#                (u.get_full_name() or u.username % u.email))
#
#        # Add headers
#        po.metadata = self.metadata
#
#        # Iterate through Source Entities and create PO entries
#        stringset = SourceEntity.objects.filter(
#            resource = self.resource)
#        for string in stringset:
#            try:
#                trans = Translation.objects.get(
#                    source_entity = string,
#                    language = language,
#                    resource = self.resource,
#                    rule=5)
#            except Translation.DoesNotExist:
#                trans = None
#            entry = polib.POEntry(msgid=string.string,
#                msgstr=trans.string if trans else "")
#            entry.occurrences = list(
#                tuple(o.split(':')) for o in string.occurrences.split(', ')
#                if not string.occurrences == "")
#            if string.flags:
#                for f in string.flags.split(', '):
#                    entry.flags.append(f)
#            if string.developer_comment:
#                entry.comment = string.developer_comment
#            if string.pluralized:
#                plurals = Translation.objects.filter(
#                    resource = self.resource,
#                    language = language,
#                    source_entity = string)
#                plural_keys = {}
#                # last rule excluding other(5)
#                last_rule = language.get_pluralrules_numbers()[-2]
#                # Initialize all plural rules up to the last
#                for p in range(0,last_rule):
#                    plural_keys[p] = ""
#                # Fill in the ones that are translated
#                for p in plurals:
#                    plural_keys[p.rule] =  p.string
#                # Remove `other` rule and use it as plural id
#                entry.msgid_plural = plural_keys.pop(5)
#                entry.msgstr_plural = plural_keys
#            po.append(entry)
#
#        # Save compiled output
#        self.compiled = po
#        return po
#
    @need_file
    def parse_file(self, is_source=False, lang_rules=None):
        """
        Parse a PO file and create a stringset with all PO entries in the file.
        """
        stringset = StringSet()
        # For .pot files the msgid entry must be used as the translation for
        # the related language.
        if self.filename.endswith(".pot") or is_source:
            ispot = True
        else:
            ispot = False

        if lang_rules:
            nplural = len(lang_rules)
        else:
            nplural = None

        pofile = polib.pofile(self.filename)

        for entry in pofile:
            pluralized = False
            same_nplural = True

            # pass empty strings for non source files
            if not ispot and entry.msgstr in ["", None]:
                continue

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
                        if nplural != nplural_file:
                            logger.error("Passed plural rules has nplurals=%s"
                                ", but '%s' file has nplurals=%s. String '%s'"
                                "skipped." % (nplural, self.filename, nplural_file,
                                entry.msgid))
                            same_nplural = False
                    else:
                        same_nplural = False

                    if not same_nplural:
                        plural_keys = message_keys
                    else:
                        plural_keys = lang_rules

                    for n, rule in enumerate(plural_keys):
                        messages.append((rule, entry.msgstr_plural['%s' % n]))
            else:
                # Not pluralized, so no plural rules. Use 5 as 'other'.
                if ispot:
                    messages = [(5, entry.msgid)]
                else:
                    messages = [(5, entry.msgstr)]

            # Add messages with the correct number (plural)
            for number, msgstr in enumerate(messages):
                translation = GenericTranslation(entry.msgid, msgstr[1],
                    context=entry.msgctxt,
                    occurrences=', '.join(
                        [':'.join([i for i in t ]) for t in entry.occurrences]),
                    rule=msgstr[0], pluralized=pluralized)

                stringset.strings.append(translation)

            if entry.comment:
                translation.comment = entry.comment
            if entry.flags:
                translation.flags = ', '.join( f for f in entry.flags)

            if is_source:
                entry.msgstr = "%(hash)s_tr" % {'hash': md5(entry.msgid.encode('utf-8')).hexdigest()}
                if entry.msgid_plural:
                    for n, rule in enumerate(plural_keys):
                        entry.msgstr_plural['%s' % n] = ("%(hash)s_pl_%(key)s" %
                            {'hash':md5(entry.msgid_plural).hexdigest(),
                            'key': n})


        if is_source:
            self.template =  get_po_contents(pofile)

        self.stringset = stringset
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
