# -*- coding: utf-8 -*-
import os
from django.db.models import get_model
from django.conf import settings
from django.template import Library

POFileLock = get_model('locks', 'POFileLock')

register = Library()

@register.inclusion_tag('pofile_lock.html', takes_context=True)
def pofile_lock(context, pofile):
    """Display a lock with the status of the POFileLock for that POFile."""
    request = context['request']
    user = request.user
    context['is_lockable'] = POFileLock.can_lock(pofile, user)
    lock = POFileLock.objects.get_valid(pofile)
    if lock:
        context['is_unlockable'] = lock.can_unlock(user)
        context['lock'] = lock
        context['is_locked'] = True
        context['is_owner'] = (lock.owner == user)
    else:
        context['is_locked'] = False
    context['pofile'] =  pofile
    context['locks_lifetime'] = settings.LOCKS_LIFETIME / 3600
    return context

