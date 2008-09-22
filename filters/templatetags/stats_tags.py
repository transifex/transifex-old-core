from django import template
#from django.conf import settings
#from django.db import models
from django.utils.safestring import mark_safe

register = template.Library()

@register.inclusion_tag("stats/comp_stats_table.html")
def comp_stats_table(stats):


    for stat in stats:
        # TODO: it should be populated with the full lang name like
        # "Brazilian Portuguese" for the code "pt_BR"
        lang_name = stat['lang']

        # Total of strings
        total = stat['translated'] + stat['fuzzy'] + stat['untranslated']

        # Percentages
        p_translated = (stat['translated']*100)/total
        p_fuzzy = (stat['fuzzy']*100)/total
        p_untranslated = (stat['untranslated']*100)/total
        p_trans_fuzzy = p_translated + p_fuzzy

        var_update = {
                      "lang_name": lang_name,
                      "total": total,
                      "p_translated": p_translated,
                      "p_fuzzy": p_fuzzy,
                      "p_untranslated": p_untranslated,
                      "p_trans_fuzzy": p_trans_fuzzy,
                    }

        stat.update(var_update)

    return {"stats": stats}