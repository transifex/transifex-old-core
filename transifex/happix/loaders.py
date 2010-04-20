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
from languages.models import Language
from happix.utils import *
from happix.models import *

from txcommon.log import logger

def locate_source_files(directory_path, source_language=None, 
        secondary_source_languages=['en_GB', 'en_US',], format='gettext'):
    """
    Try to locate the source (template) files in directory hierarchy.
    
    Return a list with all the source files.
    """
    pass

def load_dir_hierarchy(directory_path, project, source_language=None, name=None,
        format='gettext', secondary_source_languages=['en_GB', 'en_US',]):
    """
    Attempts to load a set of pofiles to the database as ONE TResource.

    The direcotry_path should be absolute! The name is the TResource's unique
    name. If no name is given, then directory_path will be used.
    Returns a TResource instance for this resource hierarchy.
    Secondary source language codes are used as a workaround to identify the 
    source strings in the case we don't find any pot or source language file.
    """
    #XXX: Needs refactoring after the last change!!!

    if not name:
        name = directory_path
    #TODO: Language instantation should be based on caching
    if not source_language:
        source_language = Language.objects.by_code_or_alias('en')

    pofiles = []
    source_file_list = []
    if os.path.isdir(directory_path):
        if not directory_path.endswith(os.sep):
            directory_path += os.sep
        # CAUTION! os.path.dirname always needs a slash at the end!!!
        pofiles = get_files(os.path.dirname(directory_path), filefilter=".*\.po$")
        source_file_list = get_files(os.path.dirname(directory_path), filefilter=".*\.pot$")

    tres = None
    source_file = None
    length = 0

    # Firstly, try to find the pot
    # As source_file_list contains a generator we must iterate over all items 
    # to determine the length
    for item in source_file_list:
        length+=1
        source_file = item
    if length>1:
        raise Exception, "Found more than one source language files!"

    # Secondly, if we didn't find a pot, try to locate the source language file.
    translation_files = []
    for f in pofiles:
        guessed_lang = guess_language(f)
        if not source_file and guessed_lang == source_language.code:
            # Raise exception
            if source_file:
                raise Exception, "Found more than one source language files!"
            source_file = f
        else:
            translation_files.append((f, guessed_lang))

    # Thirdly, use the secondary source languages to obtain the source strings!
    if not source_file:
        for tuple_pair in translation_files:
            if tuple_pair[1] in secondary_source_languages:
                source_file = tuple_pair[0]
                #XXX We silently supposed that source_language instance is the 
                # one gotten from the source_language argument, this may not be
                # the best/correct way.
                break

    # Load the source file
    tres = TResource.objects.create_or_update_from_file(path_to_file=source_file,
               project=project, source_language=source_language, name=None,
               format=format)

    # Then load the other translation files
    for pair in translation_files:
        tres.update_translations(path_to_file=pair[0], target_language=pair[1],
                                 format=format)

    return tres


def load_source_file(url, tresource, source_language, format='gettext'):
    """
    Load a source file to the DB based on its format.
    """
    #TODO: fill in the remaining format loaders
    if format=='gettext':
        return load_gettext_source(url, tresource, source_language)
    elif format=='rails':
        return None
    elif format=='java':
        return None
    elif format=='net':
        return None
    elif format=='qt':
        return None
    elif format=='apple':
        return None


def load_gettext_source(path_to_file, tresource, source_language):
    """
    Load a set of source strings in the DB from the specified file.
    
    Return the TResource instance that has been loaded.
    """

    # Open the pofile (FYI, the return value is a list!)
    pofile = polib.pofile(path_to_file)

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
        st, st_created = SourceString.objects.get_or_create(string=content, 
            description=description,
            tresource=tresource, language=source_language,
            defaults={'position': position, 'occurrences': occurrences,
                      'flags': flags, 'developer_comment': entry.comment,
                      'plural': entry.msgid_plural})
        # Refill position correctly!
        if not st_created and st.position != position:
            st.position = position
            st.save()

    return tresource


def load_translation_file(url, tresource, target_language, source_language,
                          format='gettext'):
    """
    Load a source file to the DB based on its format.
    """
    #TODO: fill in the remaining format loaders
    if format=='gettext':
        return load_gettext_po(url, tresource, target_language, source_language)
    elif format=='rails':
        return None
    elif format=='java':
        return None
    elif format=='net':
        return None
    elif format=='qt':
        return None
    elif format=='apple':
        return None


def load_gettext_po(path_to_file, tresource, target_language,
                    source_language=None):
    """
    Load a pofile in the db.
    """

    #TODO: Language instantation should be based on caching
    if not source_language:
        source_language = Language.objects.by_code_or_alias('en')

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
                                                     tresource=tresource,
                                                     position__isnull=False)
        except SourceString.DoesNotExist:
            continue

        # Plurals processing
        # WARNING! Plural string includes the singular forms.
        if entry.msgid_plural and entry.msgstr_plural:
            msgstrs = entry.msgstr_plural
            keys = list(msgstrs)
            keys.sort()
            # Iterate through all the plural strings and store them appropriately
            for index in keys:
                msgstr = msgstrs[index]
                # WARNING!!! If there already exists the relation, update only the string.
                # This means that we override the OLD STRING and we DONT KEEP HISTORY
                pts, created = PluralTranslationString.objects.get_or_create(
                                source_string=source_string, 
                                language=target_language,
                                index=index,
                                defaults={'string' : msgstr},)
                if not created and pts.string != msgstr:
                    pts.string = msgstr
                    pts.save()

        # Get or Create the new translation strings
        # If the string is empty then continue to the next iteration
        if not entry.msgstr:
            continue

        # If we have a fuzzy translation we put it in suggestions
        if 'fuzzy' in entry.flags:
            ts, created = TranslationSuggestion.objects.get_or_create(
                    source_string=source_string, string=entry.msgstr,
                    language=target_language,)
        else:
            # WARNING!!! If there is already the relation, then update only the string.
            # This means that we override the OLD STRING and we DONT KEEP HISTORY
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
