from django import template
import os
from translations.models import Language

register = template.Library()

@register.inclusion_tag('pofile_lock.html', takes_context=True)
def pofile_lock(context, pofile):
    """Display a lock with the status of the POFileLock for that POFile."""

    context['pofile'] =  pofile
    return context
