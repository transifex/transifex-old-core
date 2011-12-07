# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from gtranslate.models import Gtranslate
import requests

def _get_canonical_name(target_lang):
    if '_' in target_lang or '-' in target_lang:
        return target_lang[:2]
    return target_lang


def autotranslate_proxy(request, project_slug):
    source_lang = request.GET.get('source')
    target_lang = request.GET.get('target')
    term = request.GET.get('q')

    if not all([source_lang, target_lang, term]):
        return HttpResponse(status=400)

    target_lang = _get_canonical_name(target_lang)
    service = get_object_or_404(Gtranslate, project__slug=project_slug)
    if service.service_type == 'GT':
        base_url = 'https://www.googleapis.com/language/translate/v2'
        params = {
            'key': service.api_key,
            'q': term,
            'source': source_lang,
            'target': target_lang,
        }
    elif service.service_type == 'BT':
        base_url = 'http://api.microsofttranslator.com/V2/Ajax.svc/TranslateArray'
        params = {
            'appId': service.api_key,
            'texts': '["' + term + '"]',
            'from': source_lang,
            'to': target_lang,
            'options': '{"State": ""}'
        }
    r = requests.get(base_url, params=params)
    return HttpResponse(r.content)


def supported_langs(request, project_slug):
    service = get_object_or_404(Gtranslate, project__slug=project_slug)
    if service.service_type == 'GT':
        base_url = 'https://www.googleapis.com/language/translate/v2/languages'
        target_lang = request.GET.get('target')
        target_lang = _get_canonical_name(target_lang)
        if not target_lang:
            return HttpResponse(status=400)
        params = {
            'key': service.api_key,
            'target': target_lang,
        }
    elif service.service_type == 'BT':
        base_url = 'http://api.microsofttranslator.com/V2/Ajax.svc/GetLanguagesForTranslate'
        params = {
            'appId': service.api_key,
        }
    r = requests.get(base_url, params=params)
    return HttpResponse(r.content)
