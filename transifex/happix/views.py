# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from actionlog.models import action_logging
from happix.models import Translation, TResource, SourceEntity, PARSERS, StorageFile
from happix.forms import TResourceForm
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
        results = Translation.objects.by_source_string_and_language(
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

def view_translation_resource(request, project_slug, tresource_slug, to_lang = 'ru'):
    _to_lang = Language.objects.by_code_or_alias(to_lang)
    tresource = TResource.objects.get(project__slug = project_slug, slug = tresource_slug)
    source_strings = SourceEntity.objects.filter(tresource = tresource)[:100]

    translated_languages = {}
    lang_counts = Translation.objects.filter(tresource=tresource).order_by("language").values("language").annotate(Count("language"))
    for lang_count in lang_counts:
        language = Language.objects.get(id = lang_count['language'])
        count = lang_count['language__count']
        translated_languages[language] = count
 
    return render_to_response("tresource.html",
        { 'project' : tresource.project,
          'tresource' : tresource,
          'languages' : Language.objects.order_by('name'),
          'translated_languages' : translated_languages },
        context_instance = RequestContext(request))


@login_required
def delete_translation_resource(request, project_slug, tresource_slug):
    """
    Delete a Translation Resource in a specific project.
    """
    tresource = get_object_or_404(TResource, project__slug = project_slug,
                                  slug = tresource_slug)
    if request.method == 'POST':
        import copy
        tresource_ = copy.copy(tresource)
        tresource.delete()

        request.user.message_set.create(
            message=_("The %s translation resource was deleted.") % tresource_.name)

        #TODO: Create the specific notice type and update all the other actions.
        # ActionLog & Notification
#        nt = 'tresource_deleted'
#        context={'tresource': tresource_}
#        action_logging(request.user, [tresource_], nt, context=context)

        return HttpResponseRedirect(reverse('project_detail', 
                                    args=[tresource.project.slug]),)
    else:
        return render_to_response(
            'tresource_confirm_delete.html', {'tresource': tresource,},
            context_instance=RequestContext(request))


@login_required
def edit_translation_resource(request, project_slug, tresource_slug):
    """
    Edit the metadata of  a Translation Resource in a specific project.
    """
    tresource = get_object_or_404(TResource, project__slug = project_slug,
                                  slug = tresource_slug)

    if request.method == 'POST':
        tresource_form = TResourceForm(request.POST, instance=tresource,) 
        if tresource_form.is_valid(): 
            tresource_new = tresource_form.save()

            # TODO: (Optional) Put some signal here to denote the udpate.

            # FIXME: enable the following actionlog
            # ActionLog & Notification
#            context = {'tresource': tresource}
#            nt = 'tresource_changed'
#            action_logging(request.user, [tresource], nt, context=context)
#            if settings.ENABLE_NOTICES:
#                txnotification.send_observation_notices_for(tresource, 
#                                    signal=nt, extra_context=context)

            return HttpResponseRedirect(reverse('project_detail',
                                        args=[tresource.project.slug]),)
    else:
        if tresource:
            initial_data = {}

        tresource_form = TResourceForm(instance=tresource)

    return render_to_response('tresource_form.html', {
        'tresource_form': tresource_form,
        'tresource': tresource,
    }, context_instance=RequestContext(request))


#from libtransifex.qt import LinguistParser

#import sys

#reload(sys) # WTF? Otherwise setdefaultencoding doesn't work

## When we open file with f = codecs.open we specifi FROM what encoding to read
## This sets the encoding for the strings which are created with f.read()
#sys.setdefaultencoding('utf-8')

#MAX_FILE_SIZE = 5000000

#def parse_file(filename):
    #parsers = [LinguistParser]
    #for parser in parsers:
        #if parser.accept(filename):
            #return parser.open(filename)
    #return None

##from django.db import transaction

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

def clone_translation(request, project_slug=None, tresource_slug=None,
            source_lang_code=None, target_lang_code=None):
    '''
    Get a tresource, a src lang and a target lang and clone all translation
    strings for the src to the target.
    '''

    tresource = TResource.objects.get(
        slug = tresource_slug,
        project__slug = project_slug
    )
    # get original translation strings
    strings = Translation.objects.filter(
                tresource = tresource,
                language__code = source_lang_code)

    target_lang = Language.objects.get(code=target_lang_code)


    # clone them in new translation
    for s in strings:
        Translation.objects.get_or_create(
                    tresource = tresource,
                    language = target_lang,
                    string = s.string,
                    source_string = s.source_string)

    return HttpResponse(status=200)

def start_new_translation(request, project_slug=None, tresource_slug=None,
                                    target_lang_code=None):
    '''
    Create new language for specified tresource
    '''

    tresource = TResource.objects.get(
        slug = tresource_slug,
        project__slug = project_slug
    )

    strings = SourceEntity.objects.filter(tresource=tresource)

    target_lang = Language.objects.get(code=target_lang_code)

    for s in strings:
        Translation.objects.get_or_create(
                    tresource = tresource,
                    language = target_lang,
                    source_string = s.source_string)
