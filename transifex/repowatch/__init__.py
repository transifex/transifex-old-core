import operator
import itertools

from django.core.mail import send_mail
from django.template import loader, Context
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _

from projects import signals
from txcommon.log import logger
from translations.models import POFile
from codebases.lib import BrowserError
from notification import models as notification
# Temporary
from txcommon import notifications as txnotification

class WatchException(StandardError):
    pass

def _notify_watchers(component, files):
    """
    Notify the watchers for a specific POFile
    """
    try:
        pofile = POFile.objects.select_related().get(component=component,
                                                     filename=files[0])
        txnotification.send_observation_notices_for(pofile,
                            signal='project_component_file_changed', 
                            extra_context={'component': component,
                                           'files': files,
                                           'pofile': pofile})
    except POFile.DoesNotExist:
        # TODO: Think about it when a POFile is deleted and recreated after 
        # the prepare repo method
        pass

def _findchangesbycomponent(component):
    """
    Looks through the watches for a specific component and
    e-mails the users watching it
    """
    from repowatch.models import Watch
    watches = Watch.objects.filter(component=component)
    repochanged = False
    changes = []
    for watch in watches:
        try:
            newrev = component.get_rev(watch.path)
            logger.debug('Repowatch revision file %s: Old: %s, New: %s' % (
                watch.path, watch.rev, newrev))
            if newrev != watch.rev:
                if not watch.path:
                    repochanged = True
                else:
                    changes.append((watch.user.all(), watch.path))
                watch.rev = newrev
                watch.save()
        except (ValueError, BrowserError):
            continue
    if changes:
        changes.sort(key=operator.itemgetter(0))
        for usergroup in itertools.groupby(changes,
            key=operator.itemgetter(0)):
            _notify_watchers(component, [change[1] for change in usergroup[1]])

def _compposthandler(sender, **kwargs):
    if 'instance' in kwargs:
        _findchangesbycomponent(kwargs['instance'])

signals.post_comp_prep.connect(_compposthandler)

watch_titles = {
    'watch_add_title': _('Watch it'),
    'watch_remove_title': _('Stop watching it'),
}
