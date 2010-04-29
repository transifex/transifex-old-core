# -*- coding: utf-8 -*-
from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.sites.models import Site
from notification  import models as notification
from txcommon.log import logger
from txcron.signals import cron_daily, cron_hourly
from teams.models import Team
from projects.models import Component
from projects.signals import pre_submit_file, post_submit_file
from webtrans.signals import webtrans_form_init, webtrans_form_done
from translations.models import POFile
from models import POFileLock, POFileLockError

# Component presubmit signal handler
# Allow only owner of the lock to submit files, otherwise throw Exception
def pre_handler(sender, instance=None, user=None, component=None, 
    filename=None, **kwargs):

    if not component or not filename or not user:
        # Invalid situation
        return

    try:
        pofile = POFile.objects.get(filename=filename, object_id=component.id)
    except POFile.DoesNotExist:
        # Such pofile doesn't exist, so it couldn't have a lock
        return

    lock = POFileLock.objects.get_valid(pofile)

    if not lock:
        # Lock doesn't exist
        return

    if lock.owner != user:
        # Lock exists and person who wants to upload is not owner of the lock
        raise PermissionDenied

# Component postsubmit signal handler
# Update the lock if user checked the checkbox
def post_handler(sender, request=None, pofile=None, instance=None, user=None, **kwargs):
    if 'lock_extend' in request.POST and request.POST['lock_extend']:
        if user:
            POFileLock.objects.create_update(pofile, user).expires

def webtrans_init_handler(sender, pofile=None, user=None, **kwargs):
    try:
        POFileLock.objects.create_update(pofile, user)
        logger.debug("lock-addon: Lock aquired/extended for user '%s' "
        "for file '%s'" % (user,pofile))
    except POFileLockError, err:
        logger.debug("lock-addon: %s" % err)
        # BUG: This doesn't work - why?
        user.message_set.create(message = _(
                "Couldn't lock file, this means that you can "
                "send files only for reviewing."))

def webtrans_done_handler(sender, pofile=None, user=None, **kwargs):
    logger.debug("lock-addon: Finished editing in Lotte")
    lock = POFileLock.objects.get_valid(pofile)
    if lock:
        lock.delete_by_user(user)

def expire_notif(sender, **kwargs):
    logger.debug("lock-addon: Sending expiration notifications...")
    if not settings.ENABLE_NOTICES:
        logger.debug("lock-addon: ENABLE_NOTICES is not enabled")
        return 
    current_site = Site.objects.get_current()
    locks = POFileLock.objects.expiring()
    nt = 'project_component_file_lock_expiring'
    for lock in locks:    
        context = { 'pofile' : lock.pofile,
                    'user': lock.owner,
                    'expires': lock.expires,
                    'component': lock.pofile.object,
                    'project' : lock.pofile.object.project,
                    'current_site' : current_site }
        logger.debug("lock-addon: Sending notification about lock: %s" % lock)
        notification.send_now([lock.owner,], nt, context)
        lock.notified = True
        lock.save()

def db_cleanup(sender, **kwargs):
    logger.debug("lock-addon: Looking for expired locks")
    locks = POFileLock.objects.expired()
    for lock in locks:
        logger.debug("lock-addon: Deleting lock: %s" % lock)
        lock.delete()

def connect():
    pre_submit_file.connect(pre_handler, sender=Component)
    post_submit_file.connect(post_handler, sender=Component)
    webtrans_form_init.connect(webtrans_init_handler)
    webtrans_form_done.connect(webtrans_done_handler)
    cron_daily.connect(db_cleanup)
    cron_hourly.connect(expire_notif)
