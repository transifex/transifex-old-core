import os
import re

from django.core.files.uploadedfile import UploadedFile

from txcommon.log import logger

class BrowserError(StandardError):
    pass

def need_codebase(fn):
    def codebase_fn(self, *args, **kw):
        if not self.codebase:
            self.init_codebase()
        return fn(self, *args, **kw)
    return codebase_fn

class BrowserMixin:
    
    """
    Implement VCS-type-agnostic browser functionality.
    
    This mixin class provides methods for reading and saving
    files, from the server filesystem, creating diffs etc.
    It is inherited by the type-specific classes, and its
    methods are common to all types which use a checkout
    directory on the local file system.
    
    """

    def get_file(self, filename):
        """Return a file pointer of the requested file."""
        path = self.filepath
        fullpath = os.path.join(path, filename)
        logger.debug('Retrieving %r' % (fullpath))
        fp = open(fullpath, 'r')
        return fp

    def get_file_contents(self, filename, decode=None):
        """Return the file contents of the requested file.
        
        If decode is specified the contents are decoded with the
        <decode> encoding.
        
        """
        fp = self.get_file(filename)
        try:
            content = fp.read()
        finally:
            fp.close()
    
        if decode:
            content = content.decode(decode)
        return content

    def save_file_contents(self, filename, contents, encode=None):
        """
        Save contents as <filename>.
        
        If encode is specified the contents are first encoded with
        the <encode> encoding.
        
        """
        fullpath = os.path.join(self.filepath, filename)
        dirpath = os.path.dirname(fullpath)
        if not os.access(dirpath, os.F_OK):
            os.makedirs(dirpath)

        fp = open(fullpath, 'w')
        try:
            if isinstance(contents, basestring):
                if encode:
                    contents = contents.encode(encode)
                logger.debug("Saving %s bytes in file %s" % (len(contents),
                    fullpath))
                fp.write(contents)
            elif isinstance(contents, (file, UploadedFile)):
                contents.seek(0)
                for chunk in contents:
                    if encode:
                        chunk = chunk.encode(encode)
                    logger.debug("Saving %s bytes in file %s" %
                                 (len(contents), fullpath))
                    fp.write(chunk)
            else:
                raise ValueError("Given content to save to %s that I don't "
                                 "know how to handle: %r" % (filename,
                                 contents))
        finally:
            fp.close()

    def diff(self, filename, content):
        """Diff the contents with the filename contents."""
        try:
            contents = self.get_file_contents(filename, decode='utf-8')
        except IOError:
            contents = ''
        lines = contents.splitlines(1)
        return ''.join(unified_diff(lines, content.splitlines(1)))

    def walk(self):
        """
        Wrapper around os.walk() function.
        
        The only differense is that the root returned is relative
        to the sresource path.
        
        """
        for root, dirs, files in os.walk(self.filepath):
            # remove sresource path to create relative path
            relative_root = root.split(self.filepath, 1)[1]
            # the first characher is '/' we need to remove it
            relative_root = relative_root[1:]
            yield relative_root, dirs, files

    #FIXME: Filtering should be put in a different method.
    def get_files(self, filefilter=None):
        """
        Return files 

        It can be used with a ``filefilter`` parameter to filter the
        output result to avoid to get all files

        """
        for rel_root, dirs, files in self.walk():
            # TODO: ignore VCS metadata
            for filename in files:
                filename = os.path.join(rel_root, filename)
                if filefilter:
                    if re.compile(filefilter).match(filename):
                        yield filename
                else:
                    yield filename                
        
    def teardown_repo(self):
        """
        Remove the local copy of the repository.
        
        Ignore any changes that have been made.
        
        """
        import shutil
        #Fail silently when the repo cannot be destroyed
        #TODO: Think about this ^^ more.
        try:
            shutil.rmtree(self.path)
        except OSError:
            pass

    def rename_repo(self, new_name):
        """Rename the directory in the filesystem of the repository."""
        import shutil
        try:
            destination = "%s/%s" % (os.path.split(self.path)[0], new_name)
            shutil.move(self.path, destination)
        except IOError:
            pass

