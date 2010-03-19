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
    key = "SITE_URL_PREFIX"

    # If settings.SITE_URL_PREFIX is defined return it
    # This should be used for production environment
    custom_url = getattr(settings, key, None)
    if custom_url:
        return {key:custom_url}

    # TODO: Generate URL based on django.contrib.sites.models.Site here

    # If HTTP_HOST is defined in META, return it with http:// prefix
    # This is used by development server
    meta = getattr(request, "META", None)
    if meta and "HTTP_HOST" in meta:
        return {key:"http://%s" % meta['HTTP_HOST']}

    # Fallback is 'http://localhost'
    # Unittests default to this
    return {key:"http://localhost"}
