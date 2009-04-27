# -*- coding: utf-8 -*-
import os
import codecs
import settings
import logging
from django.utils.translation import ugettext as _

def available_languages(localedir):
    """Return available languages in the LINGUAS file."""
    available_languages = []
    try:
        linguas = codecs.open(os.path.join(localedir, 'LINGUAS'), 'r')
        for lang in linguas.readlines():
            lang = lang.strip()
            if lang and not lang.startswith('#'):
                available_languages.append((lang,lang))
    except IOError, e:
        logging.error(_('The LINGUAS file could not be opened: %s') % e)
    return available_languages