from django import template
import os

register = template.Library()

@register.inclusion_tag('component_submit.html', takes_context=True)
def pofile_submission(context, pofile):
    """Display a submit form for that POFile."""

    context['pofile'] =  pofile
    return context
