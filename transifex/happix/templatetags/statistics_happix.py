from django import template
from translations.templatetags.statistics import StatBarsPositions

register = template.Library()

@register.simple_tag
def trans_percent(obj, lang_code):
    return obj.trans_percent(lang_code)

@register.simple_tag
def translated(obj, lang_code):
    return obj.num_translated(lang_code)

@register.simple_tag
def untranslated(obj, lang_code):
    return obj.num_untranslated(lang_code)

@register.inclusion_tag("stats_bar_simple.html")
def stats_bar_simple(stat, lang_code, width=100):
    """
    Create a HTML bar to present the statistics of an object. 

    The object should have attributes trans_percent/untrans_percent.
    Accepts an optional parameter to specify the width of the total bar.
    """

    untrans_percent = stat.untrans_percent(lang_code)
    trans_percent = stat.trans_percent(lang_code)
    return {'untrans_percent': untrans_percent,
            'trans_percent': trans_percent,
            'pos': StatBarsPositions([('trans', trans_percent),
                                      ('untrans', untrans_percent)], width),}
