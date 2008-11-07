from django import template

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
