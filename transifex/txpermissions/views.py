from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.db.models.loading import get_model
from django.utils.translation import ugettext as _
from django.template.context import RequestContext
from django.template import loader
from django.contrib.auth.decorators import login_required

from authority.models import Permission
from authority.forms import UserPermissionForm
from authority.views import get_next
from txpermissions.templatetags.txpermissions import (txadd_url_for_obj,
                                                      txrequest_url_for_obj,
                                                      txurl_for_obj)

def add_permission_or_request(request, obj, view_name, approved=False,
                   template_name = 'authority/permission_form.html',
                   extra_context={}):
    """
    View for adding either a permission or a permission request for an user.
    
    This view is a centralized place for adding permissions/requests for any 
    kind of object through the whole Transifex.
    
    Following the upstrem django-authority app, all the entries are considered 
    requests until the field approved be set to True.
    """
    codename = request.POST.get('codename', None)
    next = get_next(request, obj)

    if request.method == 'POST':
        # POST method requires a permission codename
        if codename is None:
            return HttpResponseForbidden(next)
        form = UserPermissionForm(data=request.POST, obj=obj,
                                  approved=approved, perm=codename,
                                  initial=dict(codename=codename))
        if not approved:
            # Limit permission request to current user
            form.data['user'] = request.user
        if form.is_valid():
            permission = form.save(request)
            request.user.message_set.create(
                message=_('You added a permission request.'))
            return HttpResponseRedirect(next)
    else:
        form = None

    context = {
        'form': form,
        'form_url': txurl_for_obj(view_name, obj),
        'next': next,
        'perm': codename,
        'approved': approved,
    }
    context.update(extra_context)
    return render_to_response(template_name, context,
                              context_instance=RequestContext(request))


def approve_permission_request(request, requested_permission):
    """
    View for approving or not a permission request for an user.
    
    This view is a centralized place for approving permission requests for any 
    kind of object through the whole Transifex.
    
    Following the upstrem django-authority app, all the entries are considered 
    requests until the field approved be set to True.
    """
    requested_permission.approve(request.user)
    request.user.message_set.create(
        message=_('You approved the permission request.'))
    next = get_next(request, requested_permission)
    return HttpResponseRedirect(next)


def delete_permission_or_request(request, permission, approved):
    """
    View for deleting either a permission or a permission request for an user.
    
    This view is a centralized place for deleting permission/requests for any 
    kind of object through the whole Transifex.
    
    Following the upstrem django-authority app, all the entries are considered 
    requests until the field approved be set to True.
    """
    next = request.POST.get('next', '/')

    if approved:
        msg = _('You removed the permission.')
    else:
        msg = _('You removed the permission request.')

    permission.delete()

    request.user.message_set.create(message=msg)
    return HttpResponseRedirect(next)
