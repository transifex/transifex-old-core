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

@register.inclusion_tag("stats/project_stats_table.html")
def project_stats_table(langs_stats):

    for lang_stat in langs_stats:
        """
        {'lang':'pt_BR', 'component': [{'name':'tip', 'translated':600, 'fuzzy':300, 'untranslated':100},
                                       {'name':'0.2', 'translated':1000, 'fuzzy':0, 'untranslated':0},
                                       {'name':'0.1', 'translated':333, 'fuzzy':302, 'untranslated':365}
                                      ]}
        """

        # TODO: it should be populated with the full lang name like
        # "Brazilian Portuguese" for the code "pt_BR"
        lang_name = lang_stat['lang']

        lang_stat.update({"lang_name": lang_name})

        for c in lang_stat['components']:        

            # Total of strings
            total =  c['translated'] +  c['fuzzy'] + c['untranslated']

            # Percentages
            p_translated = (c['translated']*100)/total
            p_fuzzy = (c['fuzzy']*100)/total
            p_untranslated = (c['untranslated']*100)/total
            p_trans_fuzzy = p_translated + p_fuzzy

            var_update = {
                          "total": total,
                          "p_translated": p_translated,
                          "p_fuzzy": p_fuzzy,
                          "p_untranslated": p_untranslated,
                          "p_trans_fuzzy": p_trans_fuzzy,
                        }

            c.update(var_update)

    return {"stats": langs_stats}
