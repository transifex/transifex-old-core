from django import template
from repowatch.models import Watch
from repowatch import watch_titles

register = template.Library()

@register.simple_tag
def watch_add_title():
    return watch_titles['watch_add_title']

@register.simple_tag
def watch_remove_title():
    return watch_titles['watch_remove_title']

@register.inclusion_tag('watch_toggle.html', takes_context=True)
def watch_toggle(context, stat):
    """
    Handle watch links for a POfile by the logged in user
    """
    user = context['request'].user
    try:
        #TODO: Find out a better way to do it - more efficiently
        w = Watch.objects.get(path=stat.filename, component=stat.object, 
                          user__id__exact=user.id)
        stat.watched = True
    except:
        stat.watched = False

    context['stat'] = stat
    return context
