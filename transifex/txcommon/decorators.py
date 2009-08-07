# -*- coding: utf-8 -*-
import inspect
from django.http import HttpResponseRedirect
from django.utils.http import urlquote
from django.utils.functional import wraps
from django.db.models import Model, get_model
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME

from django.shortcuts import render_to_response
from django.template import RequestContext

from authority import permissions, get_check
from authority.views import permission_denied

def user_passes_test_with_403(test_func, login_url=None):
    """
    Decorator for views that checks that the user passes the given test.
    
    Users that fail the test will be given a 403 error.
    """
    def _dec(view_func):
        def _checklogin(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            else:
                resp = render_to_response('403.html', context_instance=RequestContext(request))
                resp.status_code = 403
                return resp
        _checklogin.__doc__ = view_func.__doc__
        _checklogin.__dict__ = view_func.__dict__
        return _checklogin
    return _dec

def perm_required_with_403(perm):
    """
    Decorator for views that checks whether a user has a particular permissions
    enabled, rendering a 403 page as necessary.

    """
    return user_passes_test_with_403(lambda u: u.has_perm(perm))


def _model_lookups_handler(model_lookups, *args, **kwargs):
    """
    Private function to handle the lookup model arguments from the decorator 
    call.
    """
    
    lookup_list= []
    for model, lookup, varname in model_lookups:
        if varname not in kwargs:
            continue
        value = kwargs.get(varname, None)
        if value is None:
            continue
        if isinstance(model, basestring):
            model_class = get_model(*model.split("."))
        else:
            model_class = model
        if model_class is None:
            raise ValueError(
                "The given argument '%s' is not a valid model." % model)
        if inspect.isclass(model_class) and \
                not issubclass(model_class, Model):
            raise ValueError(
                'The argument %s needs to be a model.' % model)
        lookup_list.append((model_class, lookup, value))
    return lookup_list

def one_perm_required(perms, *model_lookups, **kwargs):
    """
    Decorator for views that checks whether an user has a particular permission
    enabled for an object or a general permission from the django permission 
    system, redirecting to the log-in page if necessary.
    
    Example::

      # Permissions required for setting stats
      pr_set_stats = (
          ('granular', 'project_permission.maintain'),
          ('general',  'projects.refresh_stats'),
         #(<perm_type>, <perm_name>),
      )
    
      @one_perm_required_or_403(pr_set_stats, 
          (Project, 'slug__contains', 'project_slug'))
      def component_set_stats(request, project_slug, component_slug):
          bla bla bla
        
    In the example above the decorator checks for the `maintain` permission
    for a Project object, taking the project_slug from the view 
    `component_set_stats`. If the user IS NOT a maintainer of that project, the
    second and general permission is checked.
    
    If at least one of the permissions checks in the list returns True, the 
    access for the user is guarantee.
    
    The permissions are checked in the same order as they are put in the tuple 
    and it is allowed to add how many permissions checks as wanted.

    """
    
    login_url = kwargs.pop('login_url', settings.LOGIN_URL)
    redirect_field_name = kwargs.pop('redirect_field_name', REDIRECT_FIELD_NAME)
    redirect_to_login = kwargs.pop('redirect_to_login', True)
    def decorate(view_func):
        def decorated(request, *args, **kwargs):
            objs = []
            if request.user.is_authenticated():
                lookup_list = _model_lookups_handler(model_lookups, *args, **kwargs)
                granted = False
                for perm_type, perm in perms:
                    if perm_type == "granular":
                        for model_class, lookup, value in lookup_list:
                            objs.append(get_object_or_404(model_class, **{lookup: value}))
                        check = get_check(request.user, perm)
                        if check is not None:
                            granted = check(*objs)
                    else:
                        if request.user.has_perm(perm):
                            granted = True
                    if granted:
                        return view_func(request, *args, **kwargs)
            if redirect_to_login:
                path = urlquote(request.get_full_path())
                tup = login_url, redirect_field_name, path
                return HttpResponseRedirect('%s?%s=%s' % tup)
            return permission_denied(request)
        return wraps(view_func)(decorated)
    return decorate

def one_perm_required_or_403(perms, *args, **kwargs):
    """
    Decorator that wraps the one_perm_required_or_403 decorator and returns a
    permission denied (403) page instead of redirecting to the login URL.
    """
    kwargs['redirect_to_login'] = False
    return one_perm_required(perms, *args, **kwargs)
