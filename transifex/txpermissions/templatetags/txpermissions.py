from django import template
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse

from authority import permissions, get_check
from authority.models import Permission
from authority.forms import UserPermissionForm

from projects.permissions import ProjectPermission

register = template.Library()

@register.simple_tag
def txadd_url_for_obj(obj):
    """ It returns the reverse url for adding permissions to an object. """
    return reverse('%s_add_permission' % obj._meta.module_name, 
                   kwargs={'%s_slug' % obj._meta.module_name: obj.slug})


@register.inclusion_tag('txpermissions/permission_delete_form.html', takes_context=True)
def txpermission_delete_form(context, obj, perm):
    """
    Renders a html form to the delete view of the given permission. Returns
    no content if the request-user has no permission to delete foreign
    permissions.
    """
    user = context['request'].user
    if user.is_authenticated():
        check = ProjectPermission(user)
        if check.maintain or user.has_perm('authority.delete_permission') or user.pk == perm.creator.pk:
            return {
                'next': context['request'].build_absolute_uri(),
                'delete_url': reverse('%s_delete_permission'  % obj._meta.module_name,
                                      kwargs={'project_slug': obj.slug, 
                                              'permission_pk': perm.pk,})
            }
    return {'delete_url': None}

@register.inclusion_tag('txpermissions/permission_form.html', takes_context=True)
def txpermission_form(context, obj, perm=None):
    """
    Renders an "add permissions" form for the given object. If no object
    is given it will render a select box to choose from.

    Syntax::

        {% txpermission_form [obj] [permission_label].[check_name] %}
        {% txpermission_form project "project_perm.add_project" %}

    """
    user = context['request'].user
    if user.is_authenticated():
        check = ProjectPermission(user)
        if check.maintain or user.has_perm('authority.add_permission'):
            return {
                'form': UserPermissionForm(perm, obj, initial=dict(codename=perm)),
                'form_url': txadd_url_for_obj(obj),
                'next': context['request'].build_absolute_uri(),
            }
    return {'form': None}




