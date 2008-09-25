import os

class BrowserError(Exception):
    pass

class VCSBrowserMixin:
    """
    Implements VCS browser functionality:
    Reading and saving files, creating diffs etc
    """

    def get_file(self, filename):
        """
        Returns a file pointer of the requested file.
        """
        fullpath = os.path.join(self.path, filename)
        fp = open(fullpath, 'r')
        return fp

    def get_file_contents(self, filename, decode=None):
        """
        Returns the file contents of the requested file.
        If decode is specified the contents are decoded whith the <decode>
        encoding.
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
        Save contents as <filename>. If encode is specified the contents are
        first encoded with the <encode> encoding.
        """
        fullpath = os.path.join(self.path, filename)
        dirpath = os.path.dirname(fullpath)
        if not os.access(dirpath, os.F_OK):
            os.makedirs(dirpath)

        if encode:
            contents = contents.encode(encode)
        fp = open(fullpath, 'w')
        try:
            fp.write(contents)
        finally:
            fp.close()

    def diff(self, filename, content):
        """
        Diff the contents with the filename contents.
        """
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
        for root, dirs, files in os.walk(self.path):
            # remove sresource path to create relative path
            relative_root = root.split(self.path, 1)[1]
            # the first characher is '/' we need to remove it
            relative_root = relative_root[1:]
            yield relative_root, dirs, files

