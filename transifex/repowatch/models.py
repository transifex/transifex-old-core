import traceback
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from projects.models import Component
from repowatch import WatchException
from translations.models import POFile
from txcommon.db.models import IntegerTupleField
from txcommon.log import logger

class WatchManager(models.Manager):
    def add_watch(self, user, component, path=None):
        """
        Adds a file or repo to the watched list

        user: django.contrib.auth.models.User requesting the watch
        component: projects.models.Component to watch
        path: Path for file to watch, or None for a repo change
        """

        watch, created = Watch.objects.get_or_create(path=path, 
                                                     component=component)
        try:
            rev = component.get_rev(path)
        except ValueError:
            logger.error(traceback.format_exc())
            raise WatchException(_('Unable to add watch for path %r') % 
                path)
        watch.rev = rev
        watch.save()
        # Adding user
        watch.user.add(user)
        watch.save()
        return watch

    def remove_watch(self, user, component, path=None):
        """
        Removes a file or repo from the watched list
        Returns Watch.DoesNotExist if the watch doesn't exist

        user: django.contrib.auth.models.User requesting the watch
        component: projects.models.Component to watch
        path: Path for file to watch, or None for a repo change
        """
        watch = self.get(user__id__exact=user.id, component=component, path=path)
        watch.user.remove(user)

    def get_watches(self, user, component):
        """
        Gets the current watches on a component by a user

        user: django.contrib.auth.models.User owning the watches
        component: projects.models.Component being watched
        """
        return self.filter(user__id__exact=user.id, component=component)

    def update_watch(self, user, component, path=None):
        """
        Updates a watch without notifying the user

        user: django.contrib.auth.models.User owning the watch
        component: projects.models.Component to watch
        path: Path for file to watch, or None for a repo change
        """
        try:
            watch = self.get(user__id__exact=user.id, component=component, path=path)
            try:
                rev = component.get_rev(path)
            except ValueError:
                pass
            watch.rev = rev
            watch.save()
        except Watch.DoesNotExist:
            pass

class Watch(models.Model):
    path = models.CharField(max_length=128, null=True, default=None,
        help_text='Path to the file within the repo, or NULL for the '
        'whole repo')
    rev = IntegerTupleField(max_length=64, null=True,
        help_text='Latest revision seen')
    component = models.ForeignKey(Component,
        help_text='Component containing the repo to watch')
    user = models.ManyToManyField(User, related_name='watches',
        help_text='User to notify upon detecting a change')

    objects = WatchManager()

    def __unicode__(self):
        if self.path is None:
            return u'repo of %s for %s' % (self.component, self.user)
        return u'%s in %s for %s' % (self.path, self.component,
            self.user)

    class Meta:
        verbose_name = _('watch')
        verbose_name_plural = _('watches')

