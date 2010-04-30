# -*- coding: utf-8 -*-
from django.db.models import Count
from django.shortcuts import render_to_response
from django.template import RequestContext
from happix.models import TranslationString, TResource, SourceString, StringSet
from languages.models import Language
from projects.models import Project

def search_translation(request):
    query_string = request.GET.get('q', "")
    source_lang = request.GET.get('source_lang',None)
    if source_lang == "any_lang":
        source_lang = None
    target_lang = request.GET.get('target_lang',None)
    if target_lang == "choose_lang" or target_lang == "any_lang":
        target_lang = None
    search_terms = query_string.split()

    results = []
    result_count = None

    if search_terms:
        #TODO: AND and OR query matching operations, icontains etc.
        # For the moment we support only exact matching queries only.
        results = TranslationString.objects.by_source_string_and_language(
                    string=query_string,
                    source_code=source_lang,
                    target_code=target_lang)
        result_count = len(results)

    return render_to_response("search_translation.html",
                              {'languages': Language.objects.all(),
                               'query': query_string, 
                               'terms': search_terms, 
                               'result_count': result_count,
                               'results': results}, 
                              context_instance = RequestContext(request))


def view_projects(request):
    projects = Project.objects.all()
    return render_to_response("projects.html",
        { 'projects' : projects },
        context_instance = RequestContext(request))

def view_project(request, project_slug):
    project = Project.objects.get(slug=project_slug)
    tresource = TResource.objects.filter(project = project)
    return render_to_response("project.html",
        { 'project' : project,
          'tresources' : tresource },
        context_instance = RequestContext(request))

def view_translation_resource(request, project_slug, tresource_slug, to_lang = 'ru'):
    _to_lang = Language.objects.by_code_or_alias(to_lang)
    tresource = TResource.objects.get(project__slug = project_slug, slug = tresource_slug)
    stringsets = StringSet.objects.filter(tresource = tresource, language = _to_lang).order_by("path")
    source_strings = SourceString.objects.filter(tresource = tresource)[:100]

    languages = []
    lang_counts = TranslationString.objects.order_by("stringset__language").values("stringset__language").annotate(Count("stringset__language"))
    for lang_count in lang_counts:
        language = Language.objects.get(id = lang_count['stringset__language'])
        count = lang_count['stringset__language__count']
        languages.append(language)
 
    strings = []
    
    for source_string in source_strings:
        try:
            translated_string = TranslationString.objects.get(source_string = source_string, stringset__language = _to_lang)
        except TranslationString.DoesNotExist:
            translated_string = "NOT TRANSLATED"
        strings.append({'from':source_string,'to':translated_string})

    return render_to_response("tresource.html",
        { 'project' : tresource.project,
          'tresource' : tresource,
          'stringsets' : stringsets,
          'strings' : strings,
          'languages' : languages },
        context_instance = RequestContext(request))
    
def view_stringset(request, project_slug, tresource_slug, stringset_path):
    tresource = TResource.objects.get(project__slug = project_slug, slug = tresource_slug)
    stringset = StringSet.objects.get(path = stringset_path, tresource = tresource)
    return render_to_response("stringset.html",
        { 'project' : tresource.project,
          'tresource' : tresource, 
          'stringset' : stringset, },
        context_instance = RequestContext(request))    