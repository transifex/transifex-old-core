import binascii

from piston import oauth
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.contrib.auth import authenticate
from django.conf import settings
from django.core.urlresolvers import get_callable
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from piston import forms
from piston.authentication import send_oauth_error, initialize_server_request, oauth_auth_view, oauth_request_token 

def oauth_auth_view(request, token, callback, params):
    form = forms.OAuthAuthenticationForm(initial={
        'oauth_token': token.key,
        'oauth_callback': token.get_callback_url() or callback,
      })

    return render_to_response('mobile/authorize_token.html',
            { 'form': form }, RequestContext(request))

@login_required(login_url='/mobile/accounts/signin/')
def oauth_user_auth(request):
    oauth_server, oauth_request = initialize_server_request(request)
    
    if oauth_request is None:
        return INVALID_PARAMS_RESPONSE
        
    try:
        token = oauth_server.fetch_request_token(oauth_request)
    except oauth.OAuthError, err:
        return send_oauth_error(err)
        
    try:
        callback = oauth_server.get_callback(oauth_request)
    except:
        callback = None
    
    if request.method == "GET":
        params = oauth_request.get_normalized_parameters()

        oauth_view = getattr(settings, 'OAUTH_AUTH_VIEW', None)
        if oauth_view is None:
            return oauth_auth_view(request, token, callback, params)
        else:
            return get_callable(oauth_view)(request, token, callback, params)
    elif request.method == "POST":
        try:
            form = forms.OAuthAuthenticationForm(request.POST)
            if form.is_valid():
                token = oauth_server.authorize_token(token, request.user)
                args = '?'+token.to_string(only_key=True)
            else:
                args = '?error=%s' % 'Access not granted by user.'
                print "FORM ERROR", form.errors
            
            if not callback:
                callback = getattr(settings, 'OAUTH_CALLBACK_VIEW')
                return get_callable(callback)(request, token)
                
            response = HttpResponseRedirect(callback+args)
                
        except oauth.OAuthError, err:
            response = send_oauth_error(err)
    else:
        response = HttpResponse('Action not allowed.')
            
    return response

@csrf_exempt
def oauth_access_token(request):
    oauth_server, oauth_request = initialize_server_request(request)
    
    if oauth_request is None:
        return INVALID_PARAMS_RESPONSE
        
    try:
        token = oauth_server.fetch_access_token(oauth_request)
        return HttpResponse(token.to_string())
    except oauth.OAuthError, err:
        return send_oauth_error(err)

INVALID_PARAMS_RESPONSE = send_oauth_error(oauth.OAuthError('Invalid request parameters.'))
