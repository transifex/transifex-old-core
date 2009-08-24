import re
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from projects.models import Project
import txcommon

register = template.Library()

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
            raise template.TemplateSyntaxError, \
                "The argument for '%s' must be an integer" % tokens[0]
        return LatestProjects(tokens[1])

register.tag('get_latest_projects', DoGetLatestProjects())


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
def homelink(text="Home"):
    """Return a link to the homepage."""
    return {'text': text}

@register.simple_tag
def txversion():
    """Return the version of Transifex"""
    return txcommon.version


class CounterNode(template.Node):
    """A template node to count how many times it was called."""
    def __init__(self):
        self.count = 0

    def render(self, context):
        self.count += 1
        return self.count

@register.tag
def counter(parser, token):
    return CounterNode()




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

    result = """<script>
                var _tyjsdf = [%s], _qplmks = [%s];
                document.write('<a href="&#x6d;&#97;&#105;&#x6c;&#000116;&#111;&#x3a;');
                for(_i=0;_i<_tyjsdf.length;_i++){document.write('&#'+_tyjsdf[_i]+';');}
                document.write('">');
                for(_i=0;_i<_qplmks.length;_i++){document.write('&#'+_qplmks[_i]+';');}
                document.write('</a>');
                </script>""" % (re.sub(r',$', '', emailArrayContent),
                                re.sub(r',$', '', textArrayContent))
    
    return mark_safe(result)

mungify.needs_autoescape = True

@register.filter
def sort(value, arg):
    keys = [k.strip() for k in arg.split(',')]
    return key_sort(value, *keys)

def key_sort(l, *keys):
    """
    Sort an iterable given an arbitary number of keys relative to it
    and return the result as a list. When a key starts with '-' the
    sorting is reversed.
    
    Example: key_sort(people, 'lastname', '-age')
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


# Temporary filter
@register.filter
def notice_type_user_filter(noticetype_list):
    """
    Filter a NoticeType list passed by parameter using the NOTICE_TYPES
    dictionary that says which notice types must be shown to the user.

    It is necessary by now until the upstream project have a model change to be 
    able to do this filtering from the database.
    """
    from txcommon.management import NOTICE_TYPES
    new_list=[]
    for nt in noticetype_list:
        for n in NOTICE_TYPES:
            if nt['notice_type'].label == n["label"] \
               and n["show_to_user"] == True:
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
