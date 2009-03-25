from django import template
import os
from translations.models import Language
from txcommon.templatetags.txcommontags import key_sort

register = template.Library()

class StatBarsPositions(dict):
    """
    Hold the positions of a number of statistic bars.

    Used to present bars for translation completion status.
    """

    class BarPos:
        def __init__(self, width, left=0):
            """Initialize a simple bar."""
            self.w = width
            self.l = left

    def __init__(self, bar_data, border=1):
        """
        A dictionary to hold the positions of named bars.
        
        Accepts an ordered list (name, bar_width) of tuples to render and
        a border to pad each consecutive non-zero-sized bar. Example:
        
        >>> pos = [('a', 2), ('b', 1), border=1]
        >>> pos['a'].w
        2
        >>> pos['b'].l   # Should return first bar width + border = 2
        3
        """
        _left = 0
        for t in bar_data:
            self[t[0]] = self.BarPos(width=t[1], left=_left)
            if t[1] > 0:
                _left+=t[1]+border

def pos_from_stat(stat, border=1):
    """Return a StatBarsPositions object for a POFile (stat)."""
    return StatBarsPositions([('trans', stat.trans_perc),
                              ('fuzzy', stat.fuzzy_perc),
                              ('untrans', stat.untrans_perc)])

## Template tags

@register.inclusion_tag('comp_stats_table.html', takes_context=True)
def comp_stats_table(context, stats):
    """
    Create a HTML table to presents the statistics of all 
    languages for a component.
    """

    context['stats'] = key_sort(stats, 'sort_id', '-trans_perc')
    return context

@register.inclusion_tag("project_stats_table.html")
def project_stats_table(project):
    """
    Create a HTML table to presents the statistics of all
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
    Create a HTML table to presents the statistics of all components 
    for a specific language.
    """

    context['stats'] = key_sort(stats, 'object.project.name', '-trans_perc')
    return context

@register.inclusion_tag("release_stats_table.html")
def release_stats_table(stats, collection, release):
    """
    Create a HTML table to presents the statistics of all languages 
    for a specific release.
    """
    return {'stats': key_sort(stats, 'language.name', '-trans_perc'),
            'collection': collection,
            'release': release}

@register.inclusion_tag("stats_bar_full.html")
def stats_bar_full(stat):
    """
    Create a HTML bar to presents the full statistics 
    """

    return {'stat': stat,
            'pos': pos_from_stat(stat),}

@register.inclusion_tag("stats_bar_trans.html")
def stats_bar_trans(stat):
    """
    Create a HTML bar to presents only the translated the statistics 
    """

    return {'stat': stat,
            'pos': pos_from_stat(stat),}


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

@register.filter  
def truncate_chars_middle(value, max_length):
    """
    Truncate a string putting dots in the its middle after a certain number of 
    characters.
    """
    value_length = len(value)
    if value_length > max_length:
        max_first = max_length/2
        div_rest = max_length%2
        truncd_val = value[:max_first-2+div_rest]
        truncd_val2 = value[-(max_first-1):] 
        return truncd_val + "..." + truncd_val2  
    return value
