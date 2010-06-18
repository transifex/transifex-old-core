from django import template
from django.utils.timesince import timesince
from languages.models import Language
from translations.templatetags.statistics import StatBarsPositions

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
    elif len(args)==3 and arg[1] == 'as':
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
                    context[self.var_name] = timesince(t.last_update)
                elif self.tag_name == 'last_committer':
                    context[self.var_name] = t.user
                elif self.tag_name == 'last_translation':
                    context[self.var_name] = t
                return ''
            if self.tag_name == 'last_translation_update':
                return timesince(t.last_update)
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
