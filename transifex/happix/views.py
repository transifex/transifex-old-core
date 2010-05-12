# -*- coding: utf-8 -*-
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from happix.models import TranslationString, TResource, SourceString, PARSERS, TranslationFile
from languages.models import Language
from projects.models import Project
from django.template.defaultfilters import slugify

def view_bootstrap(request, project_slug, storage_uuid):
    """
    Take an uploaded file and insert it into database
    """
    project = Project.objects.get(slug=project_slug)
    translation_file = TranslationFile.objects.get(
        storage_uuid = storage_uuid,
    )
    print "Bootstrapping ....", translation_file.name

 
#    created = False
#    i = 0
#    while not created:
    translation_resource, created = TResource.objects.get_or_create(
            slug = "resource-%s" % (slugify(translation_file.name)),
            name = translation_file.name,
            project = project,
    )
    if created:
        print "success"

    
    try:
	strings_added, strings_updated = translation_resource.merge_translation_file(translation_file)
    except Language.DoesNotExist:
	request.user.message_set.create(
	    message="We could not guess the language of uploaded file")
    else:          
	request.user.message_set.create(
	    message="%i added, %i updated." % (strings_added, strings_updated))

    return HttpResponseRedirect(reverse('project_detail',
	args=[project_slug]))

    return HttpResponseRedirect(reverse('project.resource',
	args=[project_slug, translation_resource.slug]))


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
    print "SESSION:",request.session
    _to_lang = Language.objects.by_code_or_alias(to_lang)
    tresource = TResource.objects.get(project__slug = project_slug, slug = tresource_slug)
#    stringsets = StringSet.objects.filter(tresource = tresource, language = _to_lang).order_by("path")
    source_strings = SourceString.objects.filter(tresource = tresource)[:100]

    translated_languages = {}
    lang_counts = TranslationString.objects.filter(tresource=tresource).order_by("language").values("language").annotate(Count("language"))
    for lang_count in lang_counts:
        language = Language.objects.get(id = lang_count['language'])
        count = lang_count['language__count']
        translated_languages[language] = count
 
    #strings = []
    
    #for source_string in source_strings:
        #try:
            #translated_string = TranslationString.objects.get(source_string = source_string, tresource = tresource, language = _to_lang)
        #except TranslationString.DoesNotExist:
            #translated_string = "NOT TRANSLATED"
        #strings.append({'from':source_string,'to':translated_string})

    return render_to_response("tresource.html",
        { 'project' : tresource.project,
          'tresource' : tresource,
          'languages' : Language.objects.order_by('name'),
          'translated_languages' : translated_languages },
        context_instance = RequestContext(request))
    
#def view_stringset(request, project_slug, tresource_slug, stringset_path):
    #tresource = TResource.objects.get(project__slug = project_slug, slug = tresource_slug)
    #stringset = StringSet.objects.get(path = stringset_path, tresource = tresource)
    #return render_to_response("stringset.html",
        #{ 'project' : tresource.project,
          #'tresource' : tresource, 
          #'stringset' : stringset, },
        #context_instance = RequestContext(request))

from libtransifex.qt import LinguistParser

import sys

reload(sys) # WTF? Otherwise setdefaultencoding doesn't work

# When we open file with f = codecs.open we specifi FROM what encoding to read
# This sets the encoding for the strings which are created with f.read()
sys.setdefaultencoding('utf-8')

MAX_FILE_SIZE = 5000000

def parse_file(filename):
    parsers = [LinguistParser]
    for parser in parsers:
        if parser.accept(filename):
            return parser.open(filename)
    return None

#from django.db import transaction

def view_translation(request, project_slug=None, tresource_slug=None, lang_code=None):
    translation_resource = TResource.objects.get(
        slug = tresource_slug,
        project__slug = project_slug
    )
    target_language = Language.objects.by_code_or_alias(lang_code)
    
    return render_to_response("stringset.html",
        { 'project' : translation_resource.project,
          'tresource' : translation_resource,
          'target_language' : target_language,
          'rows' : range(0,10),},
        context_instance = RequestContext(request))