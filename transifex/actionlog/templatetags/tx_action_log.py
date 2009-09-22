from django import template
from actionlog.models import LogEntry

register = template.Library()

class LogNode(template.Node):
    def __init__(self, limit, varname, user=None, object=None):
        self.limit, self.varname, self.object , self.user = (limit, varname,
                                                             object, user)

    def __repr__(self):
        return "<GetLog Node>"

#    def entries_for_object(self, object):
#        model = object.model
#        opts = model._meta
#        app_label = opts.app_label
#        action_list = LogEntry.objects.filter(
#            object_id = object.id,
#            content_type__id__exact = ContentType.objects.get_for_model(model).id
#        ).select_related().order_by('action_time')
#        # If no history was found, see whether this object even exists.

    def render(self, context):
        if self.user is not None:
            if not self.user.isdigit():
                self.user = context[self.user].id
            context[self.varname] = LogEntry.objects.filter(
                user__id__exact=self.user).select_related(
                'content_type', 'user')[:self.limit]
            return ''
        if self.object is not None:
            from django.contrib.contenttypes.models import ContentType
            obj = context[self.object]
            obj_id = obj.id
            ctype = ContentType.objects.get_for_model(obj)
            context[self.varname] = LogEntry.objects.filter(object_id__exact=obj_id, content_type__pk=ctype.id).select_related('content_type', 'user')[:self.limit]
            return ''
        return ''

class DoGetLog:
    """
    Populates a template variable with the log for the given criteria.

    Usage::

        {% get_log <limit> as <varname> [for object <context_var_containing_user_obj>] %}

    Examples::

        {% get_log 10 as action_log for_object foo %}
        {% get_log 10 as action_log for_user 23 %}
        {% get_log 10 as action_log for_user current_user %}

    Note that ``context_var_containing_user_obj`` can be a hard-coded integer
    (object ID) or the name of a template context variable containing the user
    object whose ID you want.
    """

    def __init__(self, tag_name):
        self.tag_name = tag_name

    def __call__(self, parser, token):
        tokens = token.contents.split()
        if len(tokens) < 4:
            raise template.TemplateSyntaxError, (
                "'%s' statements requires two arguments" % self.tag_name)
        if not tokens[1].isdigit():
            raise template.TemplateSyntaxError, (
                "First argument in '%s' must be an integer" % self.tag_name)
        if tokens[2] != 'as':
            raise template.TemplateSyntaxError, (
                "Second argument in '%s' must be 'as'" % self.tag_name)
        if len(tokens) > 4:
            if tokens[4] == 'for_user':
                return LogNode(limit=tokens[1], varname=tokens[3],
                               user=(len(tokens) > 5 and tokens[5] or None))
            elif tokens[4] == 'for_object':
                return LogNode(limit=tokens[1], varname=tokens[3],
                               object=(len(tokens) > 5 and tokens[5] or None))
            else:
                raise template.TemplateSyntaxError, (
                    "Fourth argument in '%s' must be either 'user' or "
                    "'object'" % self.tag_name)

register.tag('get_log', DoGetLog('get_log'))
