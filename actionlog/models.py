from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.admin.util import quote
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

ACTIONS = {'ADDITION': 'A',
           'CHANGE': 'C',
           'DELETION': 'D',
           'SUBMISSION': 'S'}

ACTION_CHOICES = (
    ('A', _('Addition')),
    ('C', _('Change')),
    ('D', _('Deletion')),
    ('S', _('Submission')),
)


class LogEntryManager(models.Manager):
    def log_action(self, user_id, content_type_id, object_id, object_repr,
                   action_flag, change_message=''):
        e = self.model(None, None, user_id, content_type_id,
                       smart_unicode(object_id), object_repr[:200],
                       action_flag, change_message)
        e.save()

class LogEntry(models.Model):
    action_time = models.DateTimeField(_('action time'), auto_now=True)
    user = models.ForeignKey(User, related_name="tx_actions")
    content_type = models.ForeignKey(ContentType, blank=True, null=True,
                                     related_name="tx_logentry_type")
    object_id = models.IntegerField(_('object id'), blank=True, null=True)
    object_repr = models.CharField(_('object repr'), max_length=200)
    action_flag = models.CharField(_("action flag"), max_length=1,
                                   choices=ACTION_CHOICES, db_index=True)
    change_message = models.TextField(_('change message'), blank=True)
    objects = LogEntryManager()
    class Meta:
        verbose_name = _('log entry')
        verbose_name_plural = _('log entries')
        ordering = ('-action_time',)

    def __repr__(self):
        return smart_unicode(self.action_time)

    def is_addition(self):
        return self.action_flag == ACTIONS['ADDITION']

    def is_change(self):
        return self.action_flag == ACTIONS['CHANGE']

    def is_deletion(self):
        return self.action_flag == ACTIONS['DELETION']

    def is_submission(self):
        return self.action_flag == ACTIONS['SUBMISSION']

    def get_edited_object(self):
        """Return the edited object represented by this log entry."""
        return self.content_type.get_object_for_this_type(pk=self.object_id)

    def get_edit_url(self):
        """
        Return the admin URL to edit the object represented by this log entry.
        This is relative to the Django admin index page.
        """
        #FIXME
        #return mark_safe(u"%s/%s/" % (self.content_type.model, quote(self.object_id)))
        pass


def log_addition(request, object):
    """
    Log that an object has been successfully added. 
    
    The default implementation creates an admin LogEntry object.
    """
    from actionlog.models import LogEntry, ACTIONS
    LogEntry.objects.log_action(
        user_id         = request.user.pk, 
        content_type_id = ContentType.objects.get_for_model(object).pk,
        object_id       = object.pk,
        object_repr     = force_unicode(object), 
        action_flag     = ACTIONS['ADDITION']
    )
    
def log_change(request, object, message):
    """
    Log that an object has been successfully changed. 
    
    The default implementation creates an admin LogEntry object.
    """
    from actionlog.models import LogEntry, ACTIONS
    LogEntry.objects.log_action(
        user_id         = request.user.pk, 
        content_type_id = ContentType.objects.get_for_model(object).pk, 
        object_id       = object.pk, 
        object_repr     = force_unicode(object), 
        action_flag     = ACTIONS['CHANGE'], 
        change_message  = message
    )


def log_deletion(request, object, object_repr):
    """
    Log that an object has been successfully deleted. Note that since the
    object is deleted, it might no longer be safe to call *any* methods
    on the object, hence this method getting object_repr.
    
    The default implementation creates an admin LogEntry object.
    """
    from actionlog.models import LogEntry, ACTIONS
    LogEntry.objects.log_action(
        user_id         = request.user.id,
        content_type_id = ContentType.objects.get_for_model(object).pk,
        object_id       = object.pk,
        object_repr     = object_repr,
        action_flag     = ACTIONS['DELETION']
    )


def log_submission(request, object, message):
    """
    Log that an object has been successfully submited to a repository. 
    
    The default implementation creates an admin LogEntry object.
    """
    from actionlog.models import LogEntry, ACTIONS
    LogEntry.objects.log_action(
        user_id         = request.user.pk, 
        content_type_id = ContentType.objects.get_for_model(object).pk, 
        object_id       = object.pk, 
        object_repr     = force_unicode(object), 
        action_flag     = ACTIONS['SUBMISSION'], 
        change_message  = message
    )


