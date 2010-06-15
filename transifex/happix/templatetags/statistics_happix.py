from django import template
from django.utils.timesince import timesince
from languages.models import Language
from translations.templatetags.statistics import StatBarsPositions

register = template.Library()


@register.simple_tag
def last_translation_update(obj, lang_code=None):
    t = obj.last_translation(lang_code)
    if t:
        return timesince(t.last_update)
    return ''

@register.simple_tag
def last_committer(obj, lang_code=None):
    t = obj.last_translation(lang_code)
    if t:
        return t.user
    return ''

@register.simple_tag
def last_translation(obj, lang_code=None):
    t = obj.last_translation(lang_code)
    if t:
        return t
    return ''

@register.simple_tag
def trans_percent(obj, lang_code=None):
    if isinstance(obj, Language):
        return obj.trans_percent()
    return obj.trans_percent(lang_code)

@register.simple_tag
def translated(obj, lang_code=None):
    if isinstance(obj, Language):
        return obj.num_translated()
    return obj.num_translated(lang_code)

@register.simple_tag
def untranslated(obj, lang_code=None):
    if isinstance(obj, Language):
        return obj.num_untranslated()
    return obj.num_untranslated(lang_code)

@register.inclusion_tag("stats_bar_simple.html")
def stats_bar_simple(stat, lang_code=None, width=100):
    """
    Create a HTML bar to present the statistics of an object. 

    The object should have attributes trans_percent/untrans_percent.
    Accepts an optional parameter to specify the width of the total bar.
    """
    if isinstance(stat, Language):
        untrans_percent = stat.untrans_percent()
        trans_percent = stat.trans_percent()
    else:
        untrans_percent = stat.untrans_percent(lang_code)
        trans_percent = stat.trans_percent(lang_code)
    return {'untrans_percent': untrans_percent,
            'trans_percent': trans_percent,
            'pos': StatBarsPositions([('trans', trans_percent),
                                      ('untrans', untrans_percent)], width),
            'width':width}

@register.inclusion_tag("stats_bar_actions.html")
def stats_bar_actions(stat, lang_code=None, width=100):
    """
    Create a HTML bar to present the statistics of an object. 

    The object should have attributes trans_percent/untrans_percent.
    Accepts an optional parameter to specify the width of the total bar.
    """
    if isinstance(stat, Language):
        untrans_percent = stat.untrans_percent()
        trans_percent = stat.trans_percent()
    else:
        untrans_percent = stat.untrans_percent(lang_code)
        trans_percent = stat.trans_percent(lang_code)
    return {'untrans_percent': untrans_percent,
            'trans_percent': trans_percent,
            'pos': StatBarsPositions([('trans', trans_percent),
                                      ('untrans', untrans_percent)], width),
            'width':width}
