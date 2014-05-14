# -*- coding: utf-8 -*-
"""
User related class and functions.
"""

from uuid import uuid4
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template import RequestContext

from userena.models import UserenaSignup

from transifex.txcommon.forms import GetUsernameForm

class CreateUserFromSocial(object):
    """Create local users from a social auth mechanism.

    Perform every step to create new users to the system. This is a
    wrapper around userena.
    """

    def __call__(self, *args, **kwargs):
        """Create a new user to Transifex.

        For now, this is copied from social_auth.backends.pipeline.user.
        """
        user = kwargs.get('user')
        if user is not None:
            return {'user': user}
        username = kwargs.get('username')
        if username is None:
            return None
        details = kwargs.get('details')
        if details is not None:
            email = details.get('email')
        user = UserenaSignup.objects.create_user(
            username, email, password=None, active=True, send_email=False
        )
        # Activate user automatically
        user = UserenaSignup.objects.activate_user(user, user.userena_signup.activation_key)
        return {'user': user, 'is_new': True}


create_user = CreateUserFromSocial()

def redirect_to_get_username_form(request, user=None, username=None, *args, **kwargs):
    """ Redirect user to from to enter desired username
    """
    template_name = 'txcommon/get_username.html'
    if user:
        return {'username': user.username}

    if request.method == 'POST':
        form = GetUsernameForm(request.POST)
        if form.is_valid():
            return {'username': form.cleaned_data['username']}
    else:
        form = GetUsernameForm({'username': username})

    return render_to_response(template_name, {
        'form': form
        }, context_instance=RequestContext(request))

