import datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode
from django.utils.encoding import force_unicode
from django.template import loader, Context, TemplateDoesNotExist
from django.utils.translation import get_language, activate
from notification.models import NoticeType

def _get_formatted_message(label, context):
    """
    Return a message that is a rendered template with the given context using 
    the default language of the system.
    """
    current_language = get_language()

    # Setting the environment to the default language
    activate(settings.LANGUAGE_CODE)

    c = Context(context)
    try:
        msg = loader.get_template('notification/%s/notice.html' % label).render(c)
    except TemplateDoesNotExist:
        #TODO: Maybe send an alert to the admins
        msg = None

    # Reset environment to original language
    activate(current_language)

    return msg

def _user_counting(query):
    """
    Get a LogEntry queryset and return a list of dictionaries with the
    counting of times that the users appeared on the queryset.
    
    Example of the resultant dictionary:
    [{'user__username': u'editor', 'number': 5}, 
    {'user__username': u'guest', 'number': 1}]
    """
    query_result = query.values('user__username').annotate(
        number=models.Count('user')).order_by('-number')

    # Rename key from 'user__username' to 'username'
    result=[]
    for entry in query_result:
        result.append({'username': entry['user__username'], 
                       'number': entry['number']})
    return result

class LogEntryManager(models.Manager):
    def by_object(self, obj):
        """Return LogEntries for a related object."""
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(content_type__pk=ctype.pk, object_id=obj.pk)

    def by_user(self, user):
        """Return LogEntries for a specific user."""
        return self.filter(user__pk__exact=user.pk)

    def by_object_last_week(self, obj):
        """Return LogEntries of the related object for the last week."""
        last_week_date = datetime.datetime.today() - datetime.timedelta(days=7)
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(content_type__pk=ctype.pk, object_id=obj.pk,
            action_time__gt=last_week_date)


    def for_projects_by_user(self, user):
        """Return project LogEntries for a related user."""
        ctype = ContentType.objects.get(model='project')
        return self.filter(user__pk__exact=user.pk, content_type__pk=ctype.pk)

    def all_submissions(self):
        """Return a queryset with all the submissions entries."""
        return self.filter(action_type__label='project_component_file_submitted')

    def top_submitters_by_object(self, obj, number=10):
        """
        Return a list of dicts with the ordered top submitters for an object.

        The ``obj`` parameter usually receive a Project, Component, Language 
        or a Team object.
        The ``number`` parameter can be used to set the top number. The default
        value is 10.
        """
        ctype = ContentType.objects.get_for_model(obj)
        query = self.all_submissions().filter(content_type__pk=ctype.pk, 
                                              object_id=obj.pk)

        return _user_counting(query)[:number]

    def top_submitters_by_content_type(self, obj, number=10):
        """
        Return a list of dicts with the ordered top submitters for the
        entries of the ``obj`` content type.

        The ``obj`` parameter usually receive a Project, Component, Language or
        a Team object, which is used to extract the content type. However, it 
        can also receive a string with 'app_label.model' format.
        The ``number`` parameter can be used to set the top number. The default
        value is 10.
        """
        if isinstance(obj, basestring):
            app_label, model =  obj.split('.')
            ctype = ContentType.objects.get(app_label=app_label, model=model)
        else:
            ctype = ContentType.objects.get_for_model(obj)
        query = self.all_submissions().filter(content_type__pk=ctype.pk)

        return _user_counting(query)[:number]

    def top_submitters_by_project_content_type(self, number=10):
        """
        Return a list of dicts with the ordered top submitters for the
        entries of the 'project' content type.
        """
        return self.top_submitters_by_content_type('projects.project', number)

    def top_submitters_by_team_content_type(self, number=10):
        """
        Return a list of dicts with the ordered top submitters for the
        entries of the 'team' content type.
        """
        return self.top_submitters_by_content_type('teams.team', number)

    def top_submitters_by_language_content_type(self, number=10):
        """
        Return a list of dicts with the ordered top submitters for the
        entries of the 'language' content type.
        """
        return self.top_submitters_by_content_type('languages.language', number)

class LogEntry(models.Model):
    """A Entry in an object's log."""
    user = models.ForeignKey(User, blank=True, null=True, 
                             related_name="tx_user_action")

    object_id = models.IntegerField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True,
                                     related_name="tx_object")

    action_type = models.ForeignKey(NoticeType)
    action_time = models.DateTimeField()
    object_name = models.CharField(blank=True, max_length=200)
    message = models.TextField(blank=True, null=True)

    # Managers
    objects = LogEntryManager()
    
    class Meta:
        verbose_name = _('log entry')
        verbose_name_plural = _('log entries')
        ordering = ('-action_time',)

    def __unicode__(self):
        return u'%s.%s.%s' % (self.action_type, self.object_name, self.user)

    def __repr__(self):
        return smart_unicode("<LogEntry %d (%s)>" % (self.id,
                                                     self.action_type.label))

    def save(self, *args, **kwargs):
        """Save the object in the database."""
        if self.action_time is None:
           self.action_time = datetime.datetime.now()
        super(LogEntry, self).save(*args, **kwargs)

    def message_safe(self):
        """Return the message as HTML"""
        return self.message
    message_safe.allow_tags = True
    message_safe.admin_order_field = 'message'

    @property
    def action_type_short(self):
        """
        Return a shortened, generalized version of an action type.
        
        Useful for presenting an image signifying an action type. Example::
        
        >>> print l.action_type
        <NoticeType: project_component_added>
        >>> print l.action_type_short
        u'added'
        """
        return self.action_type.label.split('_')[-1]

def action_logging(user, object_list, action_type, message=None, context=None):
    """
    Add ActionLog using a set of parameters.
    
    user:
      The user that did the action.
    object_list:
      A list of objects that should be created the actionlog for.
    action_type:
      Label of a type of action from the NoticeType model.
    message:
      A message to be included at the actionlog. If no message is passed
      it will try do render a message using the notice.html from the
      notification application.
    context:
      To render the message using the notification files, sometimes it is 
      necessary to pass some vars by using a context.

    Usage::

        al = 'project_component_added'
        context = {'component': object}
        action_logging(request.user, [object], al , context=context):
    """

    if context is None:
        context = {}

    if message is None:
        message = _get_formatted_message(action_type, context)

    action_type_obj = NoticeType.objects.get(label=action_type)

    time = datetime.datetime.now()

    try:
        for object in object_list:
            l = LogEntry(
                    user_id = user.pk, 
                    content_type = ContentType.objects.get_for_model(object),
                    object_id = object.pk,
                    object_name = force_unicode(object)[:200], 
                    action_type = action_type_obj,
                    action_time = time,
                    message = message)
            l.save()
    except TypeError:
        raise TypeError("The 'object_list' parameter must be iterable")
