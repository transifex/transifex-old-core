import os
import re

from django.core.files.uploadedfile import UploadedFile

from txcommon.log import logger

def save_file(fullpath, contents, encode=None):
    """
    Save contents as <fullpath>.
    
    If encode is specified the contents are first encoded with
    the <encode> encoding.
    
    """
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
                fp.write(chunk)
        else:
            raise ValueError("Given content to save to %s that I don't "
                             "know how to handle: %r" % (fullpath,
                             contents))
    finally:
        fp.close()
