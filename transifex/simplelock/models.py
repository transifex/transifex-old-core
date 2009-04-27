from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

class LockManager(models.Manager):
    def get_for_object(self, obj):
        """Create a queryset matching all objects associated with the obj."""
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(content_type__pk=ctype.pk,
                           object_id=obj.pk)

class Lock(models.Model):
    """
    A lock on something.
    
    This usually denotes something that someone is working on and shouldn't
    be touched by others.
    """
    name = models.CharField(null=True, max_length=255)
    enabled = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    owner = models.ForeignKey(User)

    # Managers
    objects = LockManager()

    def __unicode__(self):
        return u"%(owner)s (%(name)s)" % {
            'owner': self.owner,
            'name': self.name,}

    class Meta:
        abstract = True
        verbose_name = _('Lock')
        verbose_name_plural = _('Locks')
        ordering  = ('-created',)
        get_latest_by = 'created'
