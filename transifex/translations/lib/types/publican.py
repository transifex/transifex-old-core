import os, codecs
from django.conf import settings

from translations.lib.types.pot import POTManager

class PotDirError(StandardError):
    pass

class PublicanManager(POTManager):
    """A browser class for PO files on Publican like structure."""

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


    def pot_dir_position(self):
        """
        Return the index position of the 'pot' dir in the file_set.

        Example: pot/manual/file.pot -> ['pot', 'manual', 'file.pot']
                 It retuns 0 as the index position.

        Have a 'pot' dir name in the file_set is mandatory.
        """

        # Get the first pot file that it can find
        pot_file = None
        for f in self.file_set:
            f = '/%s' % f
            if '/pot/' in f and f.endswith('.pot'):
                pot_file = f
                break
        try:
            dirs = pot_file.split('/')
            index=0
            # Find the index of 'pot' dir name in that pot file path
            for d in dirs:
                if d == 'pot':
                    return index
                index = index+1
        except AttributeError:
            raise PotDirError("There is no 'pot' directory named in the set "
                              "of files.")


    def get_langs_from_makefile(self):
        """
        Return the languages available in the OTHER_LANGS setting of the 
        Makefile. Case it does not exist return an empty list.

        Makefile setting example:

            OTHER_LANGS = as-IN bn-IN da de-DE el es-ES
        """
        for filename in self.file_set:
            if 'Makefile' in filename:
                try:
                    makefile = codecs.open(os.path.join(self.path, filename), 'r')
                    for l in makefile.readlines():
                        l = l.strip()
                        if l and not l.startswith('#'):
                            if 'OTHER_LANGS' in l:
                                return l.split('=')[1].split()
                except IOError, e:
                    logging.error('The Makefile file could not be opened: %s' % e)
        return []


    def guess_language(self, filepath, pot_dir_index=None):
        """
        Guess a language code from a filepath by finding the 'pot' dir position

        The method for looking for the language code consist on finding a 
        'pot' dir in the file_set and return the dir name of the same position 
        from filepath, using it as the language code name:

        Example: pot/manual/file.pot -> ['pot', 'manual', 'file.pot']
                 pt-BR/manual/file.po  -> ['pt-BR', 'manual', 'file.pot']

        Splitting the path the 'pot' dir can be found in the position/index
        0 of the list of dir names. In this case for the filepath passed 
        by parameter, it will be returned the dir name positioned in same
        index (pt-BR).

        Another example:
                 /foo/pot/file.pot (index 1)
                 /foo/bar/file.po -> bar
        """
        if not pot_dir_index:
            pot_dir_index = self.pot_dir_position()
        filepath = '/%s' % filepath
        return os.path.basename(filepath.split('/')[pot_dir_index])


    def get_langs(self):
        """
        Return either the langs present in the OTHER_LANGS setting of the 
        Makefile or all langs that have a po file for a object.
        """
        langs = self.get_langs_from_makefile()
        if langs:
            return langs
        else:
            pot_dir_index = self.pot_dir_position()
            for filepath in self.get_po_files():
                lang_code = self.guess_language(filepath, pot_dir_index)
                if lang_code not in langs:
                    langs.append(lang_code)
            langs.sort()
        return langs