# -*- coding: utf-8 -*-
from django.conf import settings

def site_section(request):
    """
    Return a ContextProcessor containing the first part in the URL.
    
    Eg. Templates accessed at URLs under '/projects/...' having the
    RequestContext processor will have a ``site_section`` variable available. 
    """

    try:
        ret = request.path.split('/')[1]
    except IndexError:
        ret = ''
    return { 'site_section': ret }

def site_url_prefix_processor(request):
    """
    Inserts context variable SITE_URL_PREFIX for absolute URLs
    """
    return {"SITE_URL_PREFIX" : request.build_absolute_uri("") }