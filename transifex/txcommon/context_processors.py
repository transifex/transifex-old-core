# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import translation

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
    return {"SITE_URL_PREFIX" : request.build_absolute_uri("/")[:-1] }


def bidi(request):
    """Adds to the context BiDi related variables

    LANGUAGE_DIRECTION -- Direction of current language ('ltr' or 'rtl')
    """
    if translation.get_language_bidi():
        extra_context = { 'LANGUAGE_DIRECTION':'rtl', }
    else:
        extra_context = { 'LANGUAGE_DIRECTION':'ltr', }
    return extra_context
