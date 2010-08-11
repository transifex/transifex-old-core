# -*- coding: utf-8 -*-
class Meta:
    author = "Andreas Loupasakis"
    title = "Transifex Core String Level Engine"
    description = "Adds database storage for Translations and Source Strings."

# Cache keys used
CACHE_KEYS = {
    "word_count": "wcount.%s.%s",
    "source_strings_count": "sscount.%s.%s"
}
