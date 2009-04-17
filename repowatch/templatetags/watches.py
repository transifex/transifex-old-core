from django.core.urlresolvers import reverse
from django import template
from translations.models import POFile
from projects.models import Project
from repowatch import watch_titles

register = template.Library()

@register.simple_tag
def watch_add_title():
    return watch_titles['watch_add_title']

@register.simple_tag
def watch_remove_title():
    return watch_titles['watch_remove_title']

@register.inclusion_tag('watch_toggle.html', takes_context=True)
def watch_toggle(context, obj):
    """
    Handle watch links for objects by the logged in user
    """
    if isinstance(obj, Project):
        obj.toggle_watch_url = reverse('project_toggle_watch', 
                                       args=(obj.slug,))
        obj.is_project = True

    elif isinstance(obj, POFile):
        obj.toggle_watch_url = reverse('component_toggle_watch',
                                       args=(obj.object.project.slug, 
                                       obj.object.slug, obj.filename,))
        obj.is_pofile = True

    user = context['request'].user
    obj.is_watched = obj.is_watched_by(user)
    context['obj'] = obj
    return context
