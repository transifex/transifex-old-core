from django import template

from repowatch import watch_titles

register = template.Library()

@register.simple_tag
def watch_add_title():
    return watch_titles['watch_add_title']

@register.simple_tag
def watch_remove_title():
    return watch_titles['watch_remove_title']
