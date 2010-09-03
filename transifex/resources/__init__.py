# -*- coding: utf-8 -*-
class Meta:
    author = "Andreas Loupasakis"
    title = "Transifex Core String Level Engine"
    description = "Adds database storage for Translations and Source Strings."

# Cache keys used
CACHE_KEYS = {
    "word_count": "wcount.%s.%s", # project.slug resource.slug
    "source_strings_count": "sscount.%s.%s", # project.slug resource.slug
    "lang_trans": "trans.%s.%s.%s", # lang.code project.slug resource.slug
    "lang_last_update": "update.%s.%s.%s", # lang.code project.slug resource.slug
    "available_langs": "avail_langs.%s.%s" # project.slug resource.slug
}
