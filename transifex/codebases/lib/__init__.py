import os
import re

from django.core.files.uploadedfile import UploadedFile
from django.template import Context, Template

from django.conf import settings
from txcommon.log import logger

class BrowserError(Exception):
    pass

class BrowserMixinBase:

    """
    Implement Filesystem-based type-agnostic browser functionality.

    This mixin class provides methods for reading and saving
    files, creating diffs etc. that can be used directly in 
    any directory in the filesystem.

    """

    def get_file(self, filename, path=None):
        """Return a file pointer of the requested file."""
        fullpath = os.path.join(path or self.path, filename)
        fp = open(fullpath, 'r')
        return fp

    def get_file_contents(self, filename, decode=None, path=None):
        """Return the file contents of the requested file.

        If decode is specified the contents are decoded with the
        <decode> encoding.

        """
        fp = self.get_file(filename, path)
        try:
            content = fp.read()
        finally:
            fp.close()

        if decode:
            content = content.decode(decode)
        return content

    def save_file_contents(self, filename, contents, encode=None, path=None):
        """
        Save contents as <filename>.

        If encode is specified the contents are first encoded with
        the <encode> encoding.

        """
        fullpath = os.path.join(path or self.path, filename)
        dirpath = os.path.dirname(fullpath)
        if not os.access(dirpath, os.F_OK):
            os.makedirs(dirpath)

        fp = open(fullpath, 'w')
        try:
            logger.debug("Saving %s bytes in file %s" % (len(contents), fullpath))
            if isinstance(contents, basestring):
                if encode:
                    contents = contents.encode(encode)
                fp.write(contents)
            elif isinstance(contents, (file, UploadedFile)):
                contents.seek(0)
                for chunk in contents:
                    if encode:
                        chunk = chunk.encode(encode)
                    fp.write(chunk)
            else:
                raise ValueError("Given content to save to %s that I don't "
                                 "know how to handle: %r" % (filename,
                                 contents))
        finally:
            fp.close()

    def diff(self, filename, content, path=None):
        """Diff the contents with the filename contents."""
        try:
            contents = self.get_file_contents(filename, decode='utf-8', path=path)
        except IOError:
            contents = ''
        lines = contents.splitlines(1)
        return ''.join(unified_diff(lines, content.splitlines(1)))

    def valid_filename(self, filename, filefilter=None):
        """
        Check if it has access to a filename checking against the 
        ``IGNORE_WILDCARD_LIST`` in settings and a ``filefilter``, if passed by
        parameter.

        Return a boolean value

        """
        filter_check = True
        if filefilter and not re.compile(filefilter).match(filename):
            filter_check = False

        return not re.compile(settings.IGNORE_WILDCARD_LIST).match(
            '/%s' % filename) and filter_check

    def walk(self, path=None):
        """
        Wrapper around os.walk() function.

        The only differense is that the root returned is relative
        to the sresource path.

        """
        for root, dirs, files in os.walk(path or self.path):
            # remove sresource path to create relative path
            relative_root = root.split(path or self.path, 1)[1]
            # the first characher is '/' we need to remove it
            relative_root = relative_root[1:]
            yield relative_root, dirs, files

    def get_files(self, filefilter=None, path=None):
        """
        Yield files for the filesystem

        It can be used with a ``filefilter`` parameter to filter the
        output result to avoid to get all files

        """
        for rel_root, dirs, files in self.walk(path):
            for filename in files:
                filename = os.path.join(rel_root, filename)

                if not self.valid_filename(filename, filefilter):
                    continue

                yield filename


class BrowserMixin(BrowserMixinBase):

    """
    Implement VCS-type-agnostic browser functionality.

    This mixin class provides methods for reading and saving
    files, from the server filesystem, creating diffs etc.
    It is inherited by the type-specific classes, and its
    methods are common to all types which use a checkout
    directory on the local file system.

    """

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

    def _get_user(self, user):
        if hasattr(settings, 'VCS_USER_TEMPLATE'):
            template = Template(settings.VCS_USER_TEMPLATE)
            context = Context({'user': user})
            header = template.render(context)
        else:
            if user.first_name:
                name = ' '.join((user.first_name, user.last_name))
            else:
                name = user.username
            header = '%s <%s>' % (name, user.email)
        return header
