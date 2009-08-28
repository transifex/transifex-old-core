import os, commands, re
import polib
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from translations.lib.types import (TransManagerMixin, TransManagerError)
from translations.models import POFile, Language
from translations.lib.utils import (run_command, CommandError)

class POTStatsError(Exception):

    def __init__(self, language):
        self.language = language

    def __str__(self):
        return "Could not calculate the statistics using the '%s' " \
               "language." % (self.language)

class FileFilterError(Exception):

    def __str__(self):
        return "The file filter should allows the POTFILES.in file" \
               " for intltool POT-based projects."

class POTManager(TransManagerMixin):
    """A browser class for POT files."""

    def __init__(self, file_set, path, source_lang, file_filter,
        filepath=None):
        self.file_set = file_set
        if filepath is None:
            filepath = path
        self.path = filepath
        self.source_lang = source_lang
        self.file_filter = file_filter
        self.msgmerge_path = os.path.join(settings.MSGMERGE_DIR, 
                                     os.path.basename(path))

    def get_file_path(self, filename, is_msgmerged=False):
        # All the files should be in the file_set, except the intltool
        # POT file that is created by the system
        if filename in self.file_set or \
           filename.endswith('.pot') and is_msgmerged:
            if is_msgmerged:
                file_path = os.path.join(self.msgmerge_path, filename)
            else:
                file_path = os.path.join(self.path, filename)
        else:
            raise IOError("File not found.")
        return file_path

    def get_file_content(self, filename, is_msgmerged=False):
        file_path = self.get_file_path(filename, is_msgmerged)
        filef = file(file_path, 'rb')
        file_content = filef.read()
        filef.close()
        return file_content

    def get_po_entries(self, filename):
        """Return a Django form field for the component."""
        from django import forms
        if filename in self.file_set:
            file_path = os.path.join(self.msgmerge_path, filename)
            try:
                po = polib.pofile(file_path)
            except IOError:
                pass
            else:
                return po
        return None

    def get_po_files(self):
        """Return a list of PO filenames."""

        po_files = []
        for filename in self.file_set:
            if filename.endswith('.po'):
                po_files.append(filename)
        po_files.sort()
        return po_files

    def get_langfiles(self, lang):
        """Return a list with the PO filenames for a specificy language."""

        files=[]
        for filepath in self.get_po_files():
            if self.guess_language(filepath) == lang:
                files.append(filepath)
        return files

    def guess_language(self, filepath):
        """Guess a language from a filepath."""

        if 'LC_MESSAGES' in filepath:
            fp = filepath.split('LC_MESSAGES')
            return os.path.basename(fp[0][:-1:])
        else:
            return os.path.basename(filepath[:-3:])

    def get_langs(self):
        """Return all langs tha have a po file for a object."""

        langs = []
        for filepath in self.get_po_files():
            lang_code = self.guess_language(filepath)
            if lang_code not in langs:
                langs.append(lang_code)
        langs.sort()
        return langs


    def po_file_stats(self, pofile):
        """Calculate stats for a POT/PO file."""
        error = False
        pofile = os.path.join(self.msgmerge_path, pofile)

        command = "LC_ALL=C LANG=C LANGUAGE=C msgfmt --statistics" \
                  " -o /dev/null %s" % pofile
        (error, output) = commands.getstatusoutput(command)

        if error:
            error = True
    
        r_tr = re.search(r"([0-9]+) translated", output)
        r_un = re.search(r"([0-9]+) untranslated", output)
        r_fz = re.search(r"([0-9]+) fuzzy", output)

        if r_tr: translated = r_tr.group(1)
        else: translated = 0
        if r_un: untranslated = r_un.group(1)
        else: untranslated = 0
        if r_fz: fuzzy = r_fz.group(1)
        else: fuzzy = 0

        return {'translated' : int(translated),
                'fuzzy' : int(fuzzy),
                'untranslated' : int(untranslated),
                'error' : error,}

    def calculate_file_stats(self, filename, try_to_merge):
        """
        Return the statistics of a specificy file for an object after
        merging the file with the source translation file (POT), if possible.
        """
        # We might want to skip the msgmerge setting try_to_merge as False
        if try_to_merge:
            source_file = self.get_source_file_for_pofile(filename)
            (is_msgmerged, file_path) = self.msgmerge(filename, source_file)
        else:
            is_msgmerged=False
            file_path = os.path.join(self.path, filename)

        #Copy the current file (non-msgmerged) to the static dir
        if not is_msgmerged:
            self.copy_file_to_static_dir(filename)

        postats = self.po_file_stats(file_path)

        return {'trans': postats['translated'],
                'fuzzy': postats['fuzzy'],
                'untrans': postats['untranslated'],
                'error': postats['error'],
                'is_msgmerged': is_msgmerged}

    def create_lang_stats(self, lang, object, try_to_merge=True):
        """Set the statistics of a specificy language for an object."""

        for filename in self.get_langfiles(lang):
            self.create_file_stats(filename, object, try_to_merge)

    def create_file_stats(self, filename, object, try_to_merge=True):
        """Set the statistics of a specificy file for an object."""
        lang_code = self.guess_language(filename)
        try:
            ctype = ContentType.objects.get_for_model(object)
            s, created = POFile.objects.get_or_create(object_id=object.id,
                content_type=ctype, filename=filename)

            if not s.language:
                try:
                    l = Language.objects.by_code_or_alias(code=lang_code)
                    s.language=l
                except Language.DoesNotExist:
                    pass
            s.language_code = lang_code

            calcstats = True
            rev = None
            if hasattr(object, 'get_rev'):
                rev = object.get_rev(filename)
                if rev == s.rev:
                    calcstats = False

            # For intltool components that the pot file has changes, it's
            # necessary to recalc the stats even if the 'rev' is the same
            if object.i18n_type=='INTLTOOL' and try_to_merge:
                calcstats = True

            if calcstats:
                stats = self.calculate_file_stats(filename, try_to_merge)
        except POTStatsError:
            # TODO: It should probably be raised when a checkout of a 
            # module has a problem. Needs to decide what to do when it
            # happens
            calcstats = False
        if calcstats:
            s.set_stats(trans=stats['trans'], fuzzy=stats['fuzzy'], 
                untrans=stats['untrans'], error=stats['error'])
            s.is_msgmerged = stats['is_msgmerged']
            if rev:
                s.rev = rev
        return s.save()

    def stats_for_lang_object(self, lang, object):
        """Return statistics for an object in a specific language."""
        try:
            ctype = ContentType.objects.get_for_model(object)
            return POFile.objects.filter(language=lang, content_type=ctype, 
                                         object_id=object.id)[0]
        except IndexError:
            return None

    def get_stats(self, object):
        """Return a list of statistics of languages for an object."""
        return POFile.objects.by_object_total(object)

    def delete_stats_for_object(self, object):
        """Delete all lang statistics of an object."""
        ctype = ContentType.objects.get_for_model(object)
        POFile.objects.filter(object_id=object.id, content_type=ctype).delete()

    def delete_stats_for_file_object(self, filename, object):
        """Delete a specific pofile of an object"""
        ctype = ContentType.objects.get_for_model(object)
        POFile.objects.filter(filename=filename, object_id=object.id, 
            content_type=ctype).delete()
        self.delete_file_from_static_dir(filename)

    def set_source_stats(self, object, is_msgmerged):
        """Set the source file (pot) in the database"""

        ctype = ContentType.objects.get_for_model(object)
        potfiles=self.get_source_files()
        for potfile in potfiles:
            p, created = POFile.objects.get_or_create(filename=potfile,
                                                      is_pot=True,
                                                      content_type=ctype,
                                                      object_id=object.id,
                                                      is_msgmerged=is_msgmerged)
            stats = self.po_file_stats(potfile)
            p.set_stats(trans=stats['translated'], 
                        fuzzy=stats['fuzzy'], 
                        untrans=stats['untranslated'], 
                        error=stats['error'])

            p.save()

    def get_source_stats(self, object):
        """
        Return a list of the source file (pot) statistics from the database
        """
        try:
            ctype = ContentType.objects.get_for_model(object)
            return POFile.objects.filter(object_id=object.id, 
                content_type=ctype, is_pot=True).order_by('filename')
        except POFile.DoesNotExist:
            return None

    def get_source_files(self):
        """
        Return a list with the source files (pot) paths 

        Try to find it in the file_set passed to the PO file instace. 
        If it still fails, try to find the POT file in the filesystem.
        """
        pofiles=[]
        for filename in self.file_set:
            if filename.endswith('.pot'):
                pofiles.append(filename)

        # If there is no POT in the file_set, try to find it in
        # the file system
        if not pofiles:
            filename = self.get_intltool_source_file(self.msgmerge_path)
            if filename:
                pofiles.append(filename)

        return pofiles

    def get_intltool_source_file(self, po_dir):
        """Return the POT file that might be created by intltool"""
        for root, dirs, files in os.walk(po_dir):
            for filename in files:
                if filename.endswith('.pot'):
                    # Get the relative path
                    rel_path = root.split(os.path.basename(self.path))[1]
                    # Return the relative path of the POT file without 
                    # the / in the start of the POT file path
                    return os.path.join(rel_path, filename)[1:]

    def get_source_file_for_pofile(self, filename):
        """
        Find the related source file (POT) for a pofile when it has multiple
        source files.

        This method gets a filename as parameter and tries to discover the 
        related POT file using two methods:
        
        1. Trying to find a POT file with the same base path that the pofile.
           Example: /foo/bar.pot and /foo/baz.po match on this method.

        2. Trying to find a POT file with the same domain that the pofile in any
           directory.
        
           Example: /foo/bar.pot and /foo/baz/bar.po match on this method.
           The domain in this case is 'bar'.

        If no POT is found the method returns None.
        """

        # For filename='/foo/bar.po'
        fb = os.path.basename(filename) # 'bar.po'
        fp = filename.split(fb)[0]        # '/foo/'

        source_files = self.get_source_files()

        # Find the POT with the same domain or path that the filename,
        # if the component has more that one POT file
        if len(source_files) > 1:
            for source in source_files:
                sb = os.path.basename(source)[:-1] # *.po instead *.pot
                pb = source.split(sb)[0]
                if pb==fp or sb==fb:
                    return source
        elif len(source_files) == 1:
            return source_files[0]
        else:
            return None

    def copy_file_to_static_dir(self, filename):
        """Copy a file to the destination"""
        import shutil

        dest = os.path.join(self.msgmerge_path, filename)

        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))

        shutil.copyfile(os.path.join(self.path, filename), dest)

    def delete_file_from_static_dir(self, filename):
        """Delete a file from the static cache dir"""
        dest = os.path.join(self.msgmerge_path, filename)
        try:
            os.remove(dest)
        except OSError:
            pass

    def msgmerge(self, pofile, potfile):
        """
        Merge two files and save the output at the settings.MSGMERGE_DIR.
        In case that error, copy the source file (pofile) to the 
        destination without merging.
        """
        is_msgmerged = True
        outpo = os.path.join(self.msgmerge_path, pofile)

        try:
        # TODO: Find a library to avoid call msgmerge by command
            command = "msgmerge -o %(outpo)s %(pofile)s %(potfile)s" % {
                    'outpo' : outpo,
                    'pofile' : os.path.join(self.path, pofile),
                    'potfile' : os.path.join(self.msgmerge_path, potfile),}
            
            (error, output) = commands.getstatusoutput(command)
        except:
            error = True

        if error:
            # TODO: Log this. output var can be used.
            is_msgmerged = False

        return (is_msgmerged, outpo)

    def guess_po_dir(self):
        """Guess the po/ diretory to run intltool."""
        for filename in self.file_set:
            if 'POTFILES.in' in filename:
                if self.file_filter:
                    if re.compile(self.file_filter).match(filename):
                        return os.path.join(self.path, 
                                      os.path.dirname(filename))
        raise FileFilterError

    def intltool_update(self):
        """
        Create a new POT file using "intltool-update -p" from the 
        source files. Return False if it fails.
        """
        po_dir = self.guess_po_dir()
        try:
            command = "cd \"%(dir)s\" && rm -f missing notexist && " \
                      "intltool-update -p" % { "dir" : po_dir, }
            (error, output) = commands.getstatusoutput(command)
        except:
            error = True

        # Copy the potfile if it exist to the merged files directory
        potfile = self.get_intltool_source_file(po_dir)
        if potfile:
            self.copy_file_to_static_dir(potfile)

        if error:
            # TODO: Log this. output var can be used.
            return False

        return True

    def msgfmt_check(self, po_contents):
        """
        Run a `msgfmt -c` on a file (file object).
        Raises a ValueError in case the file has errors.
        """
        try:
            p = run_command('msgfmt -o /dev/null -c -', _input=po_contents)
        except CommandError:
            # TODO: Figure out why gettext is not working here
            raise ValueError, "Your file does not" \
                            " pass by the check for correctness" \
                            " (msgfmt -c). Please run this command" \
                            " on your system to see the errors."
