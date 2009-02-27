import re
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape

import transifex

register = template.Library()

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
    return transifex.version


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
