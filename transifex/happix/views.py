# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from actionlog.models import action_logging
from happix.models import Translation, Resource, SourceEntity, PARSERS, StorageFile
from happix.forms import ResourceForm
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

def view_translation_resource(request, project_slug, resource_slug, to_lang = 'ru'):
    _to_lang = Language.objects.by_code_or_alias(to_lang)
    resource = Resource.objects.get(project__slug = project_slug, slug = resource_slug)
    source_strings = SourceEntity.objects.filter(resource = resource)[:100]

    translated_languages = {}
    lang_counts = Translation.objects.filter(resource=resource).order_by("language").values("language").annotate(Count("language"))
    for lang_count in lang_counts:
        language = Language.objects.get(id = lang_count['language'])
        count = lang_count['language__count']
        translated_languages[language] = count
 
    return render_to_response("resource.html",
        { 'project' : resource.project,
          'resource' : resource,
          'languages' : Language.objects.order_by('name'),
          'translated_languages' : translated_languages },
        context_instance = RequestContext(request))


@login_required
def delete_translation_resource(request, project_slug, resource_slug):
    """
    Delete a Translation Resource in a specific project.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                  slug = resource_slug)
    if request.method == 'POST':
        import copy
        resource_ = copy.copy(resource)
        resource.delete()

        request.user.message_set.create(
            message=_("The %s translation resource was deleted.") % resource_.name)

        #TODO: Create the specific notice type and update all the other actions.
        # ActionLog & Notification
#        nt = 'resource_deleted'
#        context={'resource': resource_}
#        action_logging(request.user, [resource_], nt, context=context)

        return HttpResponseRedirect(reverse('project_detail', 
                                    args=[resource.project.slug]),)
    else:
        return render_to_response(
            'resource_confirm_delete.html', {'resource': resource,},
            context_instance=RequestContext(request))


@login_required
def edit_translation_resource(request, project_slug, resource_slug):
    """
    Edit the metadata of  a Translation Resource in a specific project.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                  slug = resource_slug)

    if request.method == 'POST':
        resource_form = ResourceForm(request.POST, instance=resource,) 
        if resource_form.is_valid(): 
            resource_new = resource_form.save()

            # TODO: (Optional) Put some signal here to denote the udpate.

            # FIXME: enable the following actionlog
            # ActionLog & Notification
#            context = {'resource': resource}
#            nt = 'resource_changed'
#            action_logging(request.user, [resource], nt, context=context)
#            if settings.ENABLE_NOTICES:
#                txnotification.send_observation_notices_for(resource, 
#                                    signal=nt, extra_context=context)

            return HttpResponseRedirect(reverse('project_detail',
                                        args=[resource.project.slug]),)
    else:
        if resource:
            initial_data = {}

        resource_form = ResourceForm(instance=resource)

    return render_to_response('resource_form.html', {
        'resource_form': resource_form,
        'resource': resource,
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

def view_translation(request, project_slug=None, resource_slug=None, lang_code=None):
    translation_resource = Resource.objects.get(
        slug = resource_slug,
        project__slug = project_slug
    )
    target_language = Language.objects.by_code_or_alias(lang_code)
    
    return render_to_response("stringset.html",
        { 'project' : translation_resource.project,
          'resource' : translation_resource,
          'target_language' : target_language,
          'rows' : range(0,10),},
        context_instance = RequestContext(request))

def clone_translation(request, project_slug=None, resource_slug=None,
            source_lang_code=None, target_lang_code=None):
    '''
    Get a resource, a src lang and a target lang and clone all translation
    strings for the src to the target.
    '''

    resource = Resource.objects.get(
        slug = resource_slug,
        project__slug = project_slug
    )
    # get original translation strings
    strings = Translation.objects.filter(
                resource = resource,
                language__code = source_lang_code)

    target_lang = Language.objects.get(code=target_lang_code)


    # clone them in new translation
    for s in strings:
        Translation.objects.get_or_create(
                    resource = resource,
                    language = target_lang,
                    string = s.string,
                    source_string = s.source_string)

    return HttpResponse(status=200)

def start_new_translation(request, project_slug=None, resource_slug=None,
                                    target_lang_code=None):
    '''
    Create new language for specified resource
    '''

    resource = Resource.objects.get(
        slug = resource_slug,
        project__slug = project_slug
    )

    strings = SourceEntity.objects.filter(resource=resource)

    target_lang = Language.objects.get(code=target_lang_code)

    for s in strings:
        Translation.objects.get_or_create(
                    resource = resource,
                    language = target_lang,
                    source_string = s.source_string)
