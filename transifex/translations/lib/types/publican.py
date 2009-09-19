import os, codecs
from django.conf import settings

from translations.lib.types.pot import POTManager

class PotDirError(StandardError):
    pass

class PublicanManager(POTManager):
    """A browser class for PO files on Publican like structure."""

    pot_dir_index = None

    def pot_dir_position(self):
        """
        Return the index position of the 'pot' dir in the file_set.

        Example: pot/manual/file.pot -> ['pot', 'manual', 'file.pot']
                 It retuns 0 as the index position.

        Have a 'pot' dir name in the file_set is mandatory.

        """
        # If it was already found, return it
        if self.pot_dir_index:
            return self.pot_dir_index

        # Get the first pot file that it can find
        pot_file = None
        for f in self.get_files(self.file_filter):
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
                    self.pot_dir_index = index
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
        for filename in self.get_files(self.file_filter):
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


    def guess_language(self, filepath):
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
        filepath = '/%s' % filepath
        return os.path.basename(filepath.split('/')[self.pot_dir_position()])


    def get_langs(self):
        """
        Return either the langs present in the OTHER_LANGS setting of the 
        Makefile or all langs that have a po file for a object.
        """
        langs = self.get_langs_from_makefile()
        if langs:
            return langs
        else:
            for filepath in self.get_po_files():
                lang_code = self.guess_language(filepath)
                if lang_code not in langs:
                    langs.append(lang_code)
            langs.sort()
        return langs