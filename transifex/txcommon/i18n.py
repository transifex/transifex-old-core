# -*- coding: utf-8 -*-
import os
import codecs
import settings
import logging
from django.utils.translation import ugettext as _

def available_languages(localedir):
    """Return available languages in the LINGUAS file."""
    available_languages = []
    linguas_file = os.path.join(localedir, 'LINGUAS')
    try:
        linguas = codecs.open(linguas_file, 'r')
        for lang in linguas.readlines():
            lang = lang.strip()
            if lang and not lang.startswith('#'):
                available_languages.append((lang,lang))
    except IOError, e:
        logging.error(_('The LINGUAS file (%(file)s) could not be opened: %(exc)s') % 
                        {'file': linguas_file,
                         'exc': e})
    return available_languages
