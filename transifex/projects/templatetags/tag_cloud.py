import random
from math import log
from django.db.models import get_model
from django.template import Library, Node, TemplateSyntaxError, Variable, resolve_variable
from django.utils.translation import ugettext as _

from tagging.models import Tag, TaggedItem
from transifex.txcommon.log import logger

register = Library()

class TagObj:
    def __init__(self, name, count=None, font_size=None):
        self.name = name
        self.count = count
        self.font_size = font_size

class TagCloud(Node):
    def __init__(self, context_var, **kwargs):
        self.context_var = context_var
        self.kwargs = kwargs

    def render(self, context):
        try:
            n = 20
            minsize = 1.0
            maxsize = 1.75
            threshold = 1
            counts, taglist, tagcloud = [], [], []
            tags = Tag.objects.all()
            for tag in tags:
                count = tag.items.count()
                count >= threshold and (counts.append(count), taglist.append(tag))
            tagcount = zip(counts, taglist)
            tagcount.reverse()
            counts.reverse()
            maxcount = max(counts)
            mincount = min(counts[:n])
            constant = log(maxcount - (mincount - 1))/(maxsize - minsize or 1) or 1
            tagcount = tagcount[:n]
            random.shuffle(tagcount)
            for count, tag in tagcount:
                size = log(count - (mincount - 1))/constant + minsize
                tagcloud.append({'name':tag.name, 'count':count, 'size':round(size, 7)})
            context[self.context_var] = tagcloud
        except Exception, e:
            if e.message:
                logger.debug(e.message)
            else:
                logger.debug(e)
            context[self.context_var] = []
        return ''

def do_tag_cloud(parser, token):
    """
        {% tag_cloud_for_model blog.BlogEntry as tags %}
    """
    bits = token.contents.split()
    len_bits = len(bits)
    if len_bits != 3:
        raise TemplateSyntaxError(_('%s tag requires two arguments') % bits[0])
    if bits[1] != 'as':
        raise TemplateSyntaxError(_("first argument to %s tag must be 'as'") % bits[0])
    kwargs = {}

    return TagCloud(bits[2], **kwargs)

register.tag('tag_cloud', do_tag_cloud)
