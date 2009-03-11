from django import template
import os
from translations.models import Language

register = template.Library()

@register.inclusion_tag('comp_stats_table.html', takes_context=True)
def comp_stats_table(context, stats):
    """
    Creates a HTML table to presents the statistics of all 
    languages for a component.
    """
    context['stats'] = key_sort(stats, ('sort_id', '-trans_perc',))
    return context

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

@register.inclusion_tag('lang_stats_table.html', takes_context=True)
def lang_stats_table(context, stats):
    """
    Creates a HTML table to presents the statistics of all components 
    for a specific language.
    """

    context['stats'] = key_sort(stats, ('object.project.name', '-trans_perc'))
    return context

@register.inclusion_tag("release_stats_table.html")
def release_stats_table(stats, collection, release):
    """
    Creates a HTML table to presents the statistics of all languages 
    for a specific release.
    """
    return {'stats': key_sort(stats, ('language.name', '-trans_perc')),
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
def sort(value, arg):
    keys = [k.strip() for k in arg.split(',')]
    return key_sort(value, keys)

def key_sort(l, keys):
    """
    Sort an iterable given an arbitary number of keys relative to it
    and return the result as a list. When a key starts with '-' the
    sorting is reversed.
    
    Example: key_sort(people, ('lastname','-age'))
    """
    l = list(l)
    for key in keys:
        #Find out if we want a reversed ordering
        if key.startswith('-'):
            reverse = True
            key = key[1:]
        else:
            reverse = False
            
        attrs = key.split('.')
        def fun(x):
            # Calculate x.attr1.attr2...
            for attr in attrs:
                x = getattr(x, attr)
            # If the key attribute is a string we lowercase it
            if isinstance(x, basestring):
                x = x.lower()
            return x
        l.sort(key=fun, reverse=reverse)
    return l

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
