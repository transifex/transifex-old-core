from django import template
import os
from translations.models import Language

register = template.Library()

def pofile_lock(context, project, component, pofile):
    """Display a lock with the status of the POFileLock for that POFile."""
    return {'project': project,
            'component': component,
            'pofile': pofile,
            'current_user': context['current_user'],
            'perms': context['perms']}
register.inclusion_tag('pofile_lock.html', takes_context=True)(pofile_lock)
