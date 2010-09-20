# -*- coding: utf-8 -*-
import urllib2
from django.utils.simplejson import loads as parse_json, dumps as compile_json

class Languages:
    data = None
    @classmethod
    def pull(cls, urlbase):
        if cls.data != None: # We already have pulled languages from somewhere
            return
        fh = urllib2.urlopen("%s/api/languages/" % urlbase)
        raw = fh.read()
        fh.close()
        cls.data = parse_json(raw)
        # Some sanity checks
        assert cls.lang_alias_to_code('sr@Latin') == 'sr@latin'
        assert cls.lang_alias_to_code('et-EE') == 'et'

    @classmethod
    def lang_alias_to_code(cls, garbage):
        if not cls.data:
            raise Exception("Languages aren't pulled yet!")
        for lang in cls.data:
            if " %s " % garbage in lang['code_aliases'] or garbage == lang['code']:
                return lang['code']
        return None
