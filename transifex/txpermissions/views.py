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
from txpermissions.templatetags.txpermissions import txadd_url_for_obj


def add_permission(request, obj, extra_context={},
                   template_name='txpermissions/base_permission_form.html'):

    next = request.POST.get('next', '/')
    codename = request.POST.get('codename', None)

    if request.method == 'POST':
        form = UserPermissionForm(data=request.POST, obj=obj,
                                  perm=codename, initial={'codename': codename})
        if form.is_valid():
            form.save(request)
            request.user.message_set.create(
                message=_('You added a permission.'))
            return HttpResponseRedirect(next)
    else:
        form = None

    context = {
        'form': form,
        'form_url': txadd_url_for_obj(obj),
        'next': next,
        'perm': codename,
    }
    context.update(extra_context)

    return render_to_response(template_name, context,
                              context_instance=RequestContext(request))

def delete_permission(request, permission):
    permission.delete()
    request.user.message_set.create(
        message=_('You removed the permission.'))
    next = request.POST.get('next', '/')
    return HttpResponseRedirect(next)
