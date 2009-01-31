from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from projects.models import Component
from repowatch import WatchException

# Create your models here.

class WatchManager(models.Manager):
    def add_watch(user, component, path=None):
        watch, found = self.get_or_create(path=path, component=component,
            user=user)
        if not found:
            try:
                rev = component.get_rev(path)
            except ValueError:
                raise WatchException('Unable to add watch for path %r' % 
                    path)
            watch.rev = rev
            watch.save()
        return watch

class Watch(models.Model):
    path = models.CharField(max_length=128, null=True, default=None)
    rev = models.CommaSeparatedIntegerField(max_length=64)
    component = models.ForeignKey(Component)
    user = models.ManyToManyField(User)
    
    object = WatchManager()

    def __unicode__(self):
        if self.path is None:
            return u'repo of %s' % (self.component,)
        return u'%s in %s' % (self.path, self.component)

    class Meta:
        verbose_name = _('watch')
        verbose_name_plural = _('watches')
