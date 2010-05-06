# -*- coding: utf-8 -*-
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from happix.models import TranslationString, TResource, SourceString #, StringSet
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
#    stringsets = StringSet.objects.filter(tresource = tresource, language = _to_lang).order_by("path")
    source_strings = SourceString.objects.filter(tresource = tresource)[:100]

    languages = {}
    lang_counts = TranslationString.objects.filter(tresource=tresource).order_by("language").values("language").annotate(Count("language"))
    for lang_count in lang_counts:
        language = Language.objects.get(id = lang_count['language'])
        count = lang_count['language__count']
        languages[language] = count
 
    strings = []
    
    for source_string in source_strings:
        try:
            translated_string = TranslationString.objects.get(source_string = source_string, tresource = tresource, language = _to_lang)
        except TranslationString.DoesNotExist:
            translated_string = "NOT TRANSLATED"
        strings.append({'from':source_string,'to':translated_string})

    return render_to_response("tresource.html",
        { 'project' : tresource.project,
          'tresource' : tresource,
          'strings' : strings,
          'languages' : languages },
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

from django.db import transaction

#@transaction.commit_manually
def view_upload(request, project_slug, tresource_slug): #, filename=None, submitted_file=None):
    translation_resource = TResource.objects.get(
        slug = tresource_slug,
        project__slug = project_slug
    )
    if request.method == "POST" and \
        'submitted_file' in request.FILES:
        submitted_file = request.FILES['submitted_file']
        temp_file_path = "/tmp/%s" % submitted_file.name
        dest = open(temp_file_path, "wb+")
        total = 0
        for chunk in submitted_file.chunks():
            dest.write(chunk)
            total += len(chunk)
            if total >= MAX_FILE_SIZE:
                print "File size exceeded!"
                return HttpResponseRedirect(reverse('_project_resource',
                    args=[project_slug, tresource_slug]))
        dest.close()

        stringset = parse_file(temp_file_path)

        import uuid

        j = 1

        stats = {
            'source_strings_added' : 0,
            'translated_strings_added' : 0,
            'translated_strings_updated' : 0,
        }
        if stringset:
            try:
                target_language = Language.objects.by_code_or_alias(stringset.target_language)
            except Language.DoesNotExist:
                return None


            for i in stringset.strings:
                ss, created = SourceString.objects.get_or_create(
                    string= i.source_string, 
                    description=i.context or "None",
                    tresource=translation_resource,
                    defaults = {
                        'position' : 1,
                    }
                )


                ts, created = TranslationString.objects.get_or_create(
                    source_string=ss,
                    tresource = translation_resource,
                    language = target_language,
                    defaults={
                        'string' : i.translation_string,
                        'user' : request.user,
                    },
                ) # TODO: Update
                if created:
                    stats['translated_strings_added'] += 1
                else:
                    stats['translated_strings_updated'] += 1
                j += 1

            #transaction.commit()
            request.user.message_set.create(
                message="%(source_strings_added)i source strings added, %(translated_strings_added)i translated strings added, %(translated_strings_updated)i translated strings updated." % stats)
            return HttpResponseRedirect(reverse('_project_resource',
                args=[project_slug, tresource_slug]))


    print "Failed to parse file"
    return HttpResponseRedirect(reverse('_project_resource',
        args=[project_slug, tresource_slug]))

def view_translation(request, project_slug=None, tresource_slug=None, lang_code=None):
    translation_resource = TResource.objects.get(
        slug = tresource_slug,
        project__slug = project_slug
    )
    target_language = Language.objects.by_code_or_alias(lang_code)
    #strings = TranslationString.objects.filter(
    
    return render_to_response("stringset.html",
        { 'project' : translation_resource.project,
          'tresource' : translation_resource,
          'target_language' : target_language,
          'rows' : range(0,20),},
        context_instance = RequestContext(request))