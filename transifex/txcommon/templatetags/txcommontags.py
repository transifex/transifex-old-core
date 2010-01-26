# -*- coding: utf-8 -*-
import re
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.utils.translation import ugettext as _

from actionlog.models import LogEntry
from projects.models import Project
import txcommon

register = template.Library()

class ResolverNode(template.Node):
    """
    A small wrapper that adds a convenient resolve method.
    """
    def resolve(self, var, context):
        """Resolves a variable out of context if it's not in quotes"""
        if var is None:
            return var
        if var[0] in ('"', "'") and var[-1] == var[0]:
            return var[1:-1]
        else:
            return template.Variable(var).resolve(context)

    @classmethod
    def next_bit_for(cls, bits, key, if_none=None):
        try:
            return bits[bits.index(key)+1]
        except (ValueError, IndexError):
            return if_none


class LatestProjects(template.Node):

    def __init__(self, number=5):
        self.number = number

    def render(self, context):
        try:
            latest_projects = Project.objects.order_by('-created')[:self.number]
        except ValueError:
            latest_projects = None

        context['latest_projects'] = latest_projects
        return ''

class DoGetLatestProjects:

    def __init__(self):
        pass

    def __call__(self, parser, token):
        tokens = token.contents.split()
        if not tokens[1].isdigit():
            raise template.TemplateSyntaxError, (
                "The argument for '%s' must be an integer" % tokens[0])
        return LatestProjects(tokens[1])

register.tag('get_latest_projects', DoGetLatestProjects())


class TopTranslators(template.Node):

    @classmethod
    def handle_token(cls, parser, token):
        """Class method to parse get_top_translators."""
        tokens = token.contents.split()
        obj = None
        if not tokens[1].isdigit():
            raise template.TemplateSyntaxError, (
                "The first argument for '%s' must be an integer" % tokens[0])
        # {% get_top_translators <number_of_top_translators> %}
        if len(tokens) == 2:
            return cls(
                number = int(tokens[1]),
            )
        # {% get_top_translators <number_of_top_translators> <obj> %}
        if len(tokens) == 3:
            return cls(
                number = int(tokens[1]),
                obj = parser.compile_filter(tokens[2]),
            )
        else:
            raise template.TemplateSyntaxError("%r tag requires 1 or 2 arguments" % tokens[0])


    def __init__(self, number=None, obj=None):
        self.number = int(number)
        self.obj = obj

    def render(self, context):
        if self.obj:
            obj = self.obj.resolve(context)
            top_translators = LogEntry.objects.top_submitters_by_object(obj, self.number)
        else:
            top_translators = LogEntry.objects.top_submitters_by_project_content_type(self.number)
        context['top_translators'] = top_translators
        return ''

@register.tag
def get_top_translators(parser, token):
    """
    Return a dictionary with the top translators of the system or for a object,
    when it's passed by parameter.

    Usage::
    get_top_translators <number_of_top_translators>
    get_top_translators 10

    or

    get_top_translators <number_of_top_translators> <obj>
    get_top_translators 10 project_foo
    """
    return TopTranslators.handle_token(parser, token)



@register.inclusion_tag("common_render_metacount.html")
def render_metacount(list, countable):
    """
    Return meta-style link rendered as superscript to count something.
    
    For example, with list=['a', 'b'] and countable='boxes' return
    the HTML for "2 boxes".
    """
    count = len(list)
    if count > 1:
        return {'count': count,
                'countable': countable}

@register.inclusion_tag("common_homelink.html")
def homelink(text=_("Home")):
    """Return a link to the homepage."""
    return {'text': text}

@register.simple_tag
def txversion():
    """Return the version of Transifex"""
    return txcommon.version


class CounterNode(ResolverNode):
    """A template node to count how many times it was called."""
    
    @classmethod
    def handle_token(cls, parser, token):
        bits = token.contents.split()
        tag_name = bits[0]
        kwargs = {
            'initial': cls.next_bit_for(bits, tag_name, 0),
        }
        return cls(**kwargs)

    def __init__(self, initial):
        self.count = 0
        self.initial = initial

    def render(self, context):
        if self.count == 0 and self.initial != 0:
            try:
                initial = int(self.initial)
            except ValueError:
                initial = int(template.resolve_variable(self.initial, context))
        else:
            initial = 0

        self.count += 1 + initial
        return self.count

@register.tag
def counter(parser, token):
    """
    Return a number increasing its counting each time it's called.
    An ``initial`` value can be passed to identify from which number it should 
    start counting.
 
    Syntax::

        {% counter %}
        {% counter 20 %}

    """
    return CounterNode.handle_token(parser, token)


# Forms

@register.inclusion_tag("form_as_table_rows.html")
def form_as_table_rows(form, id=None):
    """
    Create a form using HTML table rows.
    """
    return {"form": form, "id": id}


# Email Munger by cootetom
# http://www.djangosnippets.org/snippets/1284/

@register.filter
@stringfilter
def mungify(email, text=None, autoescape=None):
    text = text or email
    
    if autoescape:
        email = conditional_escape(email)
        text = conditional_escape(text)

    emailArrayContent = ''
    textArrayContent = ''
    r = lambda c: '"' + str(ord(c)) + '",'

    for c in email: emailArrayContent += r(c)
    for c in text: textArrayContent += r(c)

    result = """<script type=\"text/javascript\">
                var _tyjsdf = [%s], _qplmks = [%s];
                document.write('<a href="&#x6d;&#97;&#105;&#x6c;&#000116;&#111;&#x3a;');
                for(_i=0;_i<_tyjsdf.length;_i++){document.write('&#'+_tyjsdf[_i]+';');}
                document.write('">');
                for(_i=0;_i<_qplmks.length;_i++){document.write('&#'+_qplmks[_i]+';');}
                document.write('<\/a>');
                </script>""" % (re.sub(r',$', '', emailArrayContent),
                                re.sub(r',$', '', textArrayContent))
    
    return mark_safe(result)

mungify.needs_autoescape = True

@register.filter
def sort(value, arg):
    keys = [k.strip() for k in arg.split(',')]
    return txcommon.utils.key_sort(value, *keys)


# Temporary filter
@register.filter
def notice_type_user_filter(noticetype_list):
    """
    Filter a NoticeType list passed by parameter using the NOTICE_TYPES
    dictionary that says which notice types must be shown to the user.

    It is necessary by now until the upstream project have a model change to be 
    able to do this filtering from the database.
    """
    from txcommon.notifications import NOTICE_TYPES
    new_list=[]
    for nt in noticetype_list:
        for n in NOTICE_TYPES:
            if nt['notice_type'].label == n["label"] and n["show_to_user"]:
                new_list.append(nt)
    return new_list

@register.filter
def in_list(value, arg):
    """Check if a value is present in a list."""
    return value in arg

@register.filter
def get_next(request):
    """Return the next path from the request."""
    try:
        next = request.GET.get('next', '')
        if not next:
            next = request.path
        return next
    except AttributeError:
        return ''

@register.filter
def strip_tags(value):
    """Return the value with HTML tags striped."""
    return txcommon.rst.strip_tags(value)

@register.filter
def as_rest_title(value, border=None):
    """
    Return a value as a restructured text header.

    border - Character to be used in the header bottom-border
    """
    return txcommon.rst.as_title(value, border)