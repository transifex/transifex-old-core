from django import template
import os
from translations.models import Language

register = template.Library()

def comp_stats_table(context, stats):
    """
    Creates a HTML table to presents the statistics of all 
    languages for a component.
    """

    return {'stats': stats,
            'current_user': context['request'].user,
            'perms': context['perms']}
register.inclusion_tag('comp_stats_table.html', takes_context=True)(comp_stats_table)

@register.inclusion_tag("project_stats_table.html")
def project_stats_table(project):
    """
    Creates a HTML table to presents the statistics of all
    Project's components and langs.
    """
    components = []
    stats = project.get_stats_dict()
    # TODO: We should have a smarter way to organize que components 
    # order to avoid this 'hacking'. Maybe find a way to keep the 
    # dictionary sorted by langs and components
    for s in stats:
        for c in stats[s]:
            components.append(c)
        return {'components': components,
                'stats': stats}

def lang_stats_table(context, stats):
    """
    Creates a HTML table to presents the statistics of all components 
    for a specific language.
    """

    return {'stats': stats,
            'current_user': context['request'].user,
            'perms': context['perms']}
register.inclusion_tag('lang_stats_table.html', takes_context=True)(lang_stats_table)

@register.inclusion_tag("release_stats_table.html")
def release_stats_table(stats, collection, release):
    """
    Creates a HTML table to presents the statistics of all languages 
    for a specific release.
    """

    return {'stats': stats,
            'collection': collection,
            'release': release}


@register.inclusion_tag("stats_bar_full.html")
def stats_bar_full(stat):
    """
    Creates a HTML bar to presents the full statistics 
    """
    return {'stat': stat}

@register.inclusion_tag("stats_bar_trans.html")
def stats_bar_trans(stat):
    """
    Creates a HTML bar to presents only the translated the statistics 
    """
    return {'stat': stat}

@register.filter
def sum_trans_fuzzy(stat):
    """
    This filter returns a sun of the translated and fuzzy percentages
    """
    return (stat.trans_perc + stat.fuzzy_perc)


@register.filter  
def truncate_chars(value, max_length):
    """
    Truncates a string after a certain number of characters.
    """
    if len(value) > max_length:  
        truncd_val = value[:max_length-1]  
        if value[max_length] != " ":  
            truncd_val = truncd_val[:truncd_val.rfind(" ")]  
        return  truncd_val + "..."  
    return value  
