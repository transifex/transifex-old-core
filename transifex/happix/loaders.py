# -*- coding: utf-8 -*-
"""
LOADERS (Load from local/remote FILE/STREAM to DB)

PO file headers Example
---------------------------------

"Project-Id-Version: el\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2010-01-06 14:19+0000\n"
"PO-Revision-Date: 2009-07-23 22:08+0200\n"
"Last-Translator: thalia papoutsaki <saliyath@gmail.com>\n"
"Language-Team: Greek <fedora-trans-el@redhat.com>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
"X-Generator: KAider 0.1\n"
"""
import os, polib, textwrap

# FIXME: specify the specific modules
from happix.models import *
from happix.utils import *

from txcommon.log import logger


def load_dir_hierarchy(directory_path, project, source_language=None, name=None,
        format='gettext'):
    """
    Attempts to load a set of pofiles to the database as one TResource.

    The direcotry_path should be absolute! The name is the TResource's unique
    name. If no name is given, then directory_path will be used.
    Returns a TResource instance for this resource hierarchy.
    """

    if not name:
        name = directory_path
    #TODO: Language instantation should be based on caching
    if not source_language:
        source_language = Language.objects.by_code_or_alias('en')

    if os.path.isdir(directory_path):
        if not directory_path.endswith(os.sep):
            directory_path += os.sep
        # CAUTION! os.path.dirname always needs a slash at the end!!!
        pofiles = get_files(os.path.dirname(directory_path), filefilter=".*\.po$")

    tres = None
    pre_allocation_len = 0

    source_file = None
    translation_files = []
    for f in pofiles:
        guessed_lang = guess_language(f)
        if guessed_lang == source_language.code:
            source_file = f
        else:
            translation_files.append((f, guessed_lang))

    # First load the source file
    tres = load_gettext_source(path_to_file=source_file, project=project,
        source_language=source_language, name=name)

    # Then load the other translation files
    for pair in translation_files:
        tres = load_gettext_po(path_to_file=pair[0], tresource=tres,
                               target_language=pair[1],
                               source_language=source_language)

    return tres


def load_tresource(uri):
    pass

def load_file(url, target_language, source_language, name=None):
    pass

def load_gettext_source(path_to_file, project, source_language=None, name=None):
    """
    Load or update a source pofile (may be pot) in the db.
    
    Return the TResource instance that has been loaded
    """
    if not name:
        name = path_to_file
    #TODO: Language instantation should be based on caching
    if not source_language:
        source_language = Language.objects.by_code_or_alias('en')

    # Get or Create the resource instance.
    tres, created = TResource.objects.get_or_create(name=name,
                        path=path_to_file,
                        project=project, 
                        defaults={'source_language':source_language})

    # Open the pofile (FYI, the return value is a list!)
    pofile = polib.pofile(path_to_file)

    # Reset the positions which are currently put.
    if not created:
        SourceString.objects.filter(tresource=tres,
            language=source_language,).update(position=None)

    for position, entry in enumerate(pofile):
        # If msgid is empty continue to the next iteration
        content=entry.msgid
        if not entry.msgid:
            continue
        # Get the description
        description = entry.msgctxt or ''

        # occurrences (with text wrapping as xgettext does)
        ret = []
        if entry.occurrences:
            wrapwidth = 78
            filelist = []
            for fpath, lineno in entry.occurrences:
                if lineno:
                    filelist.append('%s:%s' % (fpath, lineno))
                else:
                    filelist.append(fpath)
            filestr = ' '.join(filelist)
            if wrapwidth > 0 and len(filestr)+3 > wrapwidth:
                # XXX textwrap split words that contain hyphen, this is not 
                # what we want for filenames, so the dirty hack is to 
                # temporally replace hyphens with a char that a file cannot 
                # contain, like "*"
                lines = textwrap.wrap(filestr.replace('-', '*'),
                                        wrapwidth,
                                        initial_indent='#: ',
                                        subsequent_indent='#: ',
                                        break_long_words=False)
                # end of the replace hack
                for line in lines:
                    ret.append(line.replace('*', '-'))
            else:
                ret.append('#: '+filestr)
        occurrences = '\n'.join(ret)

        # flags
        ret = []
        if entry.flags:
            flags = []
            # Remove the fuzzy flags as it is not a translation :)
            try:
                entry.flags.remove('fuzzy')
            except ValueError:
                # There is no fuzzy value in flags, so go on!
                pass
            for flag in entry.flags:
                flags.append(flag)
            ret.append('#, %s' % ', '.join(flags))
        flags = '\n'.join(ret)

        # Get or create the SourceString.
        SourceString.objects.get_or_create(string=content, description=description,
            tresource=tres, language=source_language,
            defaults={'position': position, 'occurrences': occurrences,
                        'flags': flags, 'developer_comment': entry.comment})

    return tres


def load_gettext_po(path_to_file, tresource, target_language,
                    source_language=None):
    """
    Load a pofile in the db.
    """

    #TODO: Language instantation should be based on caching
    if not source_language:
        source_language = Language.objects.by_code_or_alias('en')
    target_language = Language.objects.by_code_or_alias(target_language)

    # Open the pofile (FYI, the return value is a list!)
    pofile = polib.pofile(path_to_file)

    for position, entry in enumerate(pofile):
        # If the TResource created now then fill the 
        # Check the msgids and update the existing ones, drop the others!
        # If msgid is empty continue to the next iteration
        content=entry.msgid
        if not entry.msgid:
            continue
        # Get the description
        description = entry.msgctxt or ''

        try:
            # For gettext there should only be one position per msgid,msgctxt
            source_string = SourceString.objects.get(string=content, 
                                                     description=description,
                                                     tresource=tresource)
        except SourceString.DoesNotExist:
            continue

        # Get or Create the new translation strings
        # If the string is empty then continue to the next iteration
        if not entry.msgstr:
            continue
        else:
            # WARNING!!! If there is already the relation, then update only the string.
            ts, created = TranslationString.objects.get_or_create(
                    source_string=source_string, language=target_language,
                    defaults={'string' : entry.msgstr},)
            if not created and ts.string != entry.msgstr:
                ts.string = entry.msgstr
                ts.save()

    return tresource


def load_rails_yml(path_to_file, target_language, source_language='en', name=None):
    pass

def load_apple_strings(path_to_file, target_language, source_language='en', name=None):
    pass

def load_php_ini(path_to_file, target_language, source_language='en', name=None):
    pass

def load_java_properties(path_to_file, target_language, source_language='en', name=None):
    pass

def load_qt_ts(path_to_file, target_language, source_language='en', name=None):
    pass

def load_net_resources(path_to_file, target_language, source_language='en', name=None):
    pass


def update_translation(source_string_hash, translation_string):
    #TODO: implement this
    pass
