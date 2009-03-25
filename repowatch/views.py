from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.utils import simplejson
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

import settings
from projects.models import Component
from repowatch import WatchException, watch_titles
from repowatch.models import Watch
from txcommon.decorators import perm_required_with_403
from translations.models import POFile

def watch_result(result):
    return HttpResponse(simplejson.dumps(result))

def watch_error(message, result=None):
    if result is None:
        result = {}
    result.update({
        'style': 'watch_error',
        'error': message,
    })
    return watch_result(result)

@login_required
@perm_required_with_403('repowatch.add_watch')
def watch_add(request, id):
    '''
    Add a watch for a path on a component for a specific user
    '''
    if request.method != 'POST':
        return watch_error('Must use POST to activate')
    result = {
        'style': 'watch_remove',
        'title': watch_titles['watch_remove_title'],
        'id': id,
        'url': reverse('watch_remove', args=[id]),
        'error': None,
    }
    try:
        p = POFile.objects.get(pk=id)
    except POFile.DoesNotExist:
        return watch_error('Requested file does not exist')
    try:
        Watch.objects.add_watch(request.user, p.object, p.filename)
        return watch_result(result)
    except WatchException, e:
        return watch_error(e.message, result)

@login_required
@perm_required_with_403('repowatch.add_watch')
def watch_remove(request, id):
    '''
    Remove a watch for a path on a component for a specific user
    '''
    if request.method != 'POST':
        return watch_error('Must use POST to activate')
    result = {
        'style': 'watch_add',
        'title': watch_titles['watch_add_title'],
        'id': id,
        'url': reverse('watch_add', args=[id]),
        'error': None,
    }
    try:
        p = POFile.objects.get(pk=id)
    except POFile.DoesNotExist:
        return watch_error('Requested file does not exist')
    try:
        Watch.objects.remove_watch(request.user, p.object, p.filename)
        return watch_result(result)
    except Watch.DoesNotExist:
        return watch_error(_('Watch not found'), result)
