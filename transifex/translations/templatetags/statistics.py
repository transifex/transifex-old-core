import operator
import os

from django import template

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

    def __init__(self, bar_data, width=100, border=1):
        """
        A dictionary to hold the positions of named bars.
        
        Arguments:
        
        - An ordered list of tuples (name, bar_width) to render
        - The width of the "100%" bar in pixels
        - The width of a border to pad each consecutive non-zero-sized bar
        
        Example:
        
        >>> pos = [('a', 2), ('b', 1), border=1]
        >>> pos['a'].w
        2
        >>> pos['b'].l   # Should return first bar width + border = 2
        3
        """
        innerwidth = width
        if innerwidth < 0:
            raise ValueError('Too many items (%d) for given width (%d) '
                'and border (%d)' % (len(bar_data), width, border))

        totsegwidth = reduce(operator.add, (x[1] for x in bar_data), 0)
        if totsegwidth == 0:
            # No translations whatsoever
            self['trans'] = self.BarPos(width, 0)
            self['fuzzy'] = self.BarPos(0, width)
            self['untrans'] = self.BarPos(0, width)
            return
        oldend = 0
        for segnum, segment in enumerate(bar_data):
            if segment[1] < 0:
                raise ValueError('Negative segment size (%d) given for '
                    'element %d'% (segment[1], segnum + 1))
            fl = oldend
            fr = fl + segment[1] * innerwidth
            oldend = fr
            l = int(round(float(fl) / totsegwidth))
            r = int(round(float(fr) / totsegwidth))
            self[segment[0]] = self.BarPos(r - l, l)
        return

def pos_from_stat(stat, width, border=1):
    """Return a StatBarsPositions object for a POFile (stat)."""
    return StatBarsPositions([('trans', stat.trans_perc),
                              ('fuzzy', stat.fuzzy_perc),
                              ('untrans', stat.untrans_perc)], width)

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

@register.inclusion_tag("comp_lang_stats_table.html", takes_context=True)
def comp_lang_stats_table(context, stats):
    """
    Create a HTML table to present the statistics of all files of a component
    for a specific language.
    """
    context['stats'] = key_sort(stats, 'filename', '-trans_perc')
    return context

@register.inclusion_tag("stats_bar_full.html")
def stats_bar_full(stat, width=100):
    """
    Create a HTML bar to present the full statistics. 

    Accepts an optional parameter to specify the width of the total bar.
    """

    return {'stat': stat,
            'pos': pos_from_stat(stat, width),}

@register.inclusion_tag("stats_bar_trans.html")
def stats_bar_trans(stat, width=100):
    """
    Create an HTML bar to present only the translated statistics.

    Accepts an optional parameter to specify the width of the total bar.
    """

    return {'stat': stat,
            'pos': pos_from_stat(stat, width),}


@register.inclusion_tag("source_files.html", takes_context=True)
def render_source_files(context, sources):
    """
    Create an HTML to present only the source files.
    """

    context['sources'] = sources
    return context

@register.inclusion_tag("number_range.html")
def number_range(number):
    """Return a number to group completion stats based on their number.
    
    Depending on the categories defined, different classes will be returned.
    For example, with the following constant, this will return
    'lt50' for numbers less than 50 and gt50 for numbers between 50-100.
    In the case of multiple matches, the first match is returned.
    
    RANGES = {'lt50': (0, 49),
              'gt50': (50, 100)}
    """

    RANGES = {'incomplete': (0, 99),
              'complete': (100, 100)}
    for (r, w) in RANGES.items():
        if w[0] <= number <= w[1]:
            return {'range': r }
