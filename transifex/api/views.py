# -*- coding: utf-8 -*-
# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext as _

def request_token_ready(request, token):
    error = request.GET.get('error', '')
    ctx = RequestContext(request, {
        'error' : error,
        'token' : token
    })
    return render_to_response(
        'piston/request_token_ready.html',
        context_instance = ctx
    )

def reject_legacy_api(request, *args, **kwargs):
    return HttpResponseBadRequest(_("This version of API is obsolete. "\
            "Please have a look at %(url)s for details."
            ) % {'url': 'http://help.transifex.com/features/api/'\
                    'index.html#api-index' }
    )

