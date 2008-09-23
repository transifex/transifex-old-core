from django import template
#from django.conf import settings
#from django.db import models
from django.utils.safestring import mark_safe

register = template.Library()

@register.inclusion_tag("stats/comp_stats_table.html")
def comp_stats_table(stats):

    return {"stats": stats}

@register.inclusion_tag("stats/project_stats_table.html")
def project_stats_table(project):
    
    components = []
    stats = project.get_stats()
    for s in stats:
        for c in stats[s]:
            components.append(c)
        return {'components': components,
                'stats': stats}

@register.filter
def sum_trans_fuzzy(stat):
    return (stat.trans_perc + stat.fuzzy_perc)