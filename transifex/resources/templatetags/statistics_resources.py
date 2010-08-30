import operator

from django import template
from django.utils.timesince import timesince
from languages.models import Language

register = template.Library()

def common_parser(parser, token):
    obj = None
    lang_code = None
    var_name = None
    tag_name = None
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    args = arg.split()
    # args[0] -> obj, arg[1] -> lang_code || arg[1] -> 'as', arg[2] -> 'as' || 
    # arg[2] -> var_name, arg[3] -> var_name,  
    if len(args)==4 and args[2] == 'as':
        obj = args[0]
        lang_code = args[1]
        var_name = args[3]
    elif len(args)==3 and args[1] == 'as':
        obj = args[0]
        var_name = args[2]
    elif len(args)==2:
        obj = args[0]
        lang_code = args[1]
    elif len(args)==1:
        obj = args[0]
    else:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    return tag_name, obj, lang_code, var_name


class LastTranslationNode(template.Node):
    def __init__(self, obj, lang_code=None, var_name=None, tag_name='last_translation'):
        self.obj = template.Variable(obj)
        self.lang_code = None
        if lang_code:
            self.lang_code = template.Variable(lang_code)
        self.var_name = var_name
        self.tag_name = tag_name

    def render(self, context):
        try:
            actual_obj = self.obj.resolve(context)
            actual_lang_code = None
            if self.lang_code:
                actual_lang_code = self.lang_code.resolve(context)
            t = actual_obj.last_translation(actual_lang_code)
            if not t:
                return ''
            # We have used "as"
            if self.var_name:
                if self.tag_name == 'last_translation_update':
                    context[self.var_name] = t.last_update
                elif self.tag_name == 'last_committer':
                    context[self.var_name] = t.user
                elif self.tag_name == 'last_translation':
                    context[self.var_name] = t
                return ''
            if self.tag_name == 'last_translation_update':
                return t.last_update
            elif self.tag_name == 'last_committer':
                return t.user
            elif self.tag_name == 'last_translation':
                return t
            return ''
        except template.VariableDoesNotExist:
            return ''

@register.tag
def last_translation_update(parser, token):
    tag_name, obj, lang_code, var_name = common_parser(parser, token)
    return LastTranslationNode(obj, lang_code, var_name, tag_name)

@register.tag
def last_committer(parser, token):
    tag_name, obj, lang_code, var_name = common_parser(parser, token)
    return LastTranslationNode(obj, lang_code, var_name, tag_name)

@register.tag
def last_translation(parser, token):
    tag_name, obj, lang_code, var_name = common_parser(parser, token)
    return LastTranslationNode(obj, lang_code, var_name, tag_name)


@register.simple_tag
def trans_percent(obj, lang_code=None):
    return obj.trans_percent(lang_code)

@register.simple_tag
def translated(obj, lang_code=None):
    return obj.num_translated(lang_code)

@register.simple_tag
def untranslated(obj, lang_code=None):
    return obj.num_untranslated(lang_code)


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


@register.inclusion_tag("resources/stats_bar_simple.html")
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

@register.inclusion_tag("resources/stats_bar_actions.html")
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
