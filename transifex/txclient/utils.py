# -*- coding: utf-8 -*-

from __future__ import absolute_import
from functools import wraps
from .conf import LATEST_VERSION
from .versions import user_agent, is_client_request, extract_version, \
        is_client_old
from .notify import notify_user
from .log import logger


def _process(request):
    """
    Process the request.

    Check, if the request is from an old client by checking the versions.
    """
    agent = user_agent(request)
    version = extract_version(agent)
    if is_client_old(version):
        msg = 'User %s used old client version %s.'
        logger.debug(msg % request.user.username, version)
        notify_user(request.user)


def handle_client_request(f):
    """
    Handle a client request.
    """
    @wraps(f)
    def new_f(request, *args, **kwargs):
        response = f(*args, **kwargs)
        if is_client_request(request):
            _process(request)
            response['X-Current-Client-Version'] = LATEST_VERSION
        return response
    return new_f
