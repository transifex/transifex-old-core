from exceptions import NotImplementedError
import tempfile, os, time
import zipfile, tarfile

"""
Support for handling compressed files and data.
"""

class POCompressedArchive:
    """A compressed archive with PO files inside."""
    
    SUPPORTED_TYPES = ['zip', 'targz']

    def __init__(self, pofiles, filename, type):
        tmpdir = tempfile.gettempdir()
        if type == 'zip':
            self.filename = '%s.zip' % filename
        elif type == 'targz':
            self.filename = '%s.tar.gz' % filename

        self.file_path = os.path.join(tmpdir,
                                      '%s.%s' % (self.filename, time.time()))
        if not type in self.SUPPORTED_TYPES:
            raise NotImplementedError("Unsupported archive type")
        if type == 'zip':
            self.file = zipfile.ZipFile(self.file_path, 'w')
            self.content_type = 'application/x-zip'
            for pofile in pofiles:
                path = pofile.object.trans.tm.get_file_path(pofile.filename)
                self.file.write(str(path), str(pofile.symbolic_path))
        elif type == 'targz':
            self.file = tarfile.open(self.file_path, 'w')
            self.content_type = 'application/x-gzip'
            for pofile in pofiles:
                path = pofile.object.trans.tm.get_file_path(pofile.filename)
                self.file.add(str(path), str(pofile.symbolic_path))
        self.file.close()
                
    def cleanup(self):
        os.unlink(self.file_path)
