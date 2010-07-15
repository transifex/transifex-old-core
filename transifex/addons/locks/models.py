# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django_addons.errors import AddonError
from txcommon.log import logger
from projects.permissions.project import ProjectPermission
from translations.models import POFile

class POFileLockError(AddonError):
    pass

class POFileLockManager(models.Manager):
    def get_for_object(self, obj):
        """Create a queryset matching all objects associated with the obj."""
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(content_type__pk=ctype.pk,
                           object_id=obj.pk)

    def expiring(self):
        """
        Returns list of locks that are about to expire
        """
        return self.filter(
            notified = False,
            expires__lt = datetime.now() + 
            timedelta(seconds=settings.LOCKS_EXPIRE_NOTIF))

    def expired(self):
        """
        Returns list of expired locks
        """
        return self.filter(
            expires__lt = datetime.now() )

    def valid(self):
        """
        Returns list of valid locks
        """
        return self.filter(expires__gt = datetime.now() )

    def get_valid(self, pofile):
        """
        Returns valid (not expired) lock if one exists for 'pofile'
        """
        try:
            return self.valid().get(pofile=pofile)
        except POFileLock.DoesNotExist:
            return None

    def create_update(self, pofile, user):
        """
        Creates new or updates existing lock object for 'pofile'
        * Checks wether 'user' has permissions to lock 'pofile'
        * Checks wether 'user' has reached max number of locks
        * Checks wether 'pofile' is already locked by someone else
        """

        # Permission check
        if not POFileLock.can_lock(pofile, user):
            raise POFileLockError(_("User '%(user)s' has no permission to "
               "submit files for or coordinate  '%(pofile)s'") % 
               {"user" : user, "pofile" : pofile})

        now = datetime.now()

        # Lock limit check
        if settings.LOCKS_PER_USER != None:
            locks = self.filter(
                owner = user,
                expires__gt = now) 
            if len(locks) >= settings.LOCKS_PER_USER:
                raise POFileLockError(_("User '%(user)s' already has maximum "
                "allowed %(locks)i locks.") % {"user" : user, 
                "locks" : settings.LOCKS_PER_USER})

        expires = now + timedelta(seconds=settings.LOCKS_LIFETIME)
        try:
            lock = self.get(pofile = pofile)
            # The lock is not expired and user is not the owner
            if lock.expires and lock.expires > now and lock.owner != user:
                raise POFileLockError("This file is already locked "
                    "by '%s'" % lock.owner)
            else:
                # Overwrite old owner
                lock.owner = user
            # Update expiration date
            lock.expires = expires
        except POFileLock.DoesNotExist:
            # Object didn't exist, create new one
            lock = self.create(pofile=pofile, owner=user, expires=expires)
        # Set notified flag to False meaning that expiration notification
        # has not been sent about this lock yet
        lock.notified = False
        lock.save()
        return lock

class POFileLock(models.Model):
    """
     A lock/hold on a POFile object.
    
    This usually denotes something that someone is working on and shouldn't
    be touched by others.
    """
    enabled = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    notified = models.BooleanField(default=False, help_text="Whether "
        "notification about the expiration of lock has been sent to owner")
    expires = models.DateTimeField(help_text="Time of lock expiration.")
    owner = models.ForeignKey(User)
    pofile = models.ForeignKey(POFile, related_name='locks', null=True)

    # Managers
    objects = POFileLockManager()

    def __unicode__(self):
        return u"%(pofile)s (%(owner)s)" % {
            'owner': self.owner,
            'pofile': self.pofile,}

    class Meta:
        db_table = 'addons_locks_pofile_lock'
        unique_together = ('pofile', 'owner')
        ordering  = ('-created',)
        get_latest_by = 'created'

    def can_unlock(self, user):
        """
        This function can be used to perform permission check wether 
        'user' can unlock this POFileLock instance
        """
        perm = ProjectPermission(user)
        allowed = (self.owner == user) or perm.coordinate_team( \
           project=self.pofile.object.project, language=self.pofile.language)
        return allowed

    @staticmethod
    def can_lock(pofile, user):
        """
        This function can be used to perform permission check wether
        'user' can lock 'pofile'. NB! It does not perform lock count check!
        """
        perm = ProjectPermission(user)
        allowed = perm.submit_file(pofile) or perm.coordinate_team( \
            project=pofile.object.project, language=pofile.language)
        return allowed

    def delete_by_user(self, user, *args, **kwargs):
        """
        If 'user' can remove the lock, deletes the instance of POFileLock
        """
        if not self.can_unlock(user):
            raise POFileLockError(_("User '%(user)s' is not allowed "
            "to remove lock '%(lock)s'") % { "user" : user, 
            "lock" : self})
        return super(POFileLock, self).delete(*args, **kwargs)
