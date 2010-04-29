# -*- coding: utf-8 -*-
import operator
import itertools


from txcommon.log import logger
from txcommon import notifications as txnotification
from projects.signals import pre_clear_cache, post_comp_prep
from projects.models import Component
from translations.models import POFile
from codebases.lib import BrowserError
from models import Watch

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
    watches = Watch.objects.filter(component=component)
    changes = []
    for watch in watches:
        try:
            newrev = component.get_rev(watch.path)
            logger.debug('Repowatch revision file %s: Old: %s, New: %s' % (
                watch.path, watch.rev, newrev))
            if newrev != watch.rev:
                if watch.path:
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

def comp_post_handler(sender, **kwargs):
    if 'instance' in kwargs:
        _findchangesbycomponent(kwargs['instance'])

def clear_cache_handler(sender, component = None, instance = None, **kwargs):
    Watch.objects.filter(component=instance or component).delete()

def connect():
    post_comp_prep.connect(comp_post_handler)
    pre_clear_cache.connect(clear_cache_handler, sender = Component)
