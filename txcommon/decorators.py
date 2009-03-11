# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext

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
