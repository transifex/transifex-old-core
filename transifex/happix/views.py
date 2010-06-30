# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from actionlog.models import action_logging
from happix.models import Translation, Resource, SourceEntity, PARSERS, StorageFile
from happix.forms import ResourceForm
from languages.models import Language
from projects.models import Project
from teams.models import Team

try:
    import json
except:
    import simplejson as json


def search_translation(request):
    """
    Return a set of results on translations, given a set of terms as query.
    """
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

#FIXME: permissions needed for private projects
def resource_detail(request, project_slug, resource_slug):
    """
    Return the details overview of a project resource.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                 slug = resource_slug)

    # We want the teams to check in which languages user is permitted to translate.
    user_teams = []
    if getattr(request, 'user'):
        user_teams = Team.objects.filter(project=resource.project).filter(
            Q(coordinators=request.user)|
            Q(members=request.user)).distinct()

    return render_to_response("resource.html",
        { 'project' : resource.project,
          'resource' : resource,
          'languages' : Language.objects.order_by('name'),
          'translated_languages' : resource.available_languages,
          'user_teams' : user_teams },
        context_instance = RequestContext(request))


#FIXME: permissions needed
@login_required
def resource_delete(request, project_slug, resource_slug):
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


#FIXME: permissions needed
@login_required
def resource_edit(request, project_slug, resource_slug):
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


#XXX: Obsolete
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
          'rows' : range(0,10),
          'WEBTRANS_SUGGESTIONS': settings.WEBTRANS_SUGGESTIONS},
        context_instance = RequestContext(request))


#XXX: Obsolete
def start_new_translation(request, project_slug=None, resource_slug=None,
                                    target_lang_code=None):
    '''
    Create new language for specified resource.
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


#FIXME: permissions needed for private projects
def resource_actions(request, project_slug=None, resource_slug=None,
                     target_lang_code=None):
    """
    Ajax view that returns an fancybox template snippet for resource specific 
    actions.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                 slug = resource_slug)
    target_language = get_object_or_404(Language, code=target_lang_code)
    project = resource.project
    # Get the team if exists to use it for permissions and links
    team = Team.objects.get_or_none(project, target_lang_code)

    return render_to_response("resource_actions.html",
    { 'project' : project,
      'resource' : resource,
      'target_language' : target_language,
      'team' : team},
    context_instance = RequestContext(request))


#FIXME: permissions needed for private projects
def project_resources(request, project_slug=None, offset=None, **kwargs):
    """
    Ajax view that returns a table snippet for all the resources in a project.
    
    If offset is provided, then the returned table snippet includes only the
    rows beginning from the offset and on.
    """
    more = kwargs.get('more', False)
    MORE_ENTRIES = 5
    project = get_object_or_404(Project, slug=project_slug)
    total = Resource.objects.filter(project=project).count()
    begin = int(offset)
    end_index = (begin + MORE_ENTRIES)
    resources = Resource.objects.filter(project=project)[begin:]
    # Get the slice :)
    if more and (not end_index >= total):
        resources = resources[begin:end_index]

    return render_to_response("resource_list_more.html",
    { 'project' : project,
      'resources' : resources,},
    context_instance = RequestContext(request))


#FIXME: Permissions
def clone_language(request, project_slug=None, resource_slug=None,
            source_lang_code=None, target_lang_code=None):
    '''
    Get a resource, a src lang and a target lang and clone all translation
    strings for the src to the target.
    
    The user is redirected to the online editor for the target language.
    '''

    resource = Resource.objects.get(
        slug = resource_slug,
        project__slug = project_slug
    )
    # get the strings which will be cloned
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
                    source_entity = s.source_entity,
                    number = s.number)
    return HttpResponseRedirect(reverse('translate', args=[project_slug,
                                resource_slug, target_lang_code]),)


#FIXME: permissions needed
@login_required
def translate(request, project_slug, resource_slug, lang_code,
                     *args, **kwargs):
    """
    Main lotte view.
    """

    translation_resource = Resource.objects.get(
        slug = resource_slug,
        project__slug = project_slug
    )
    target_language = Language.objects.by_code_or_alias(lang_code)

    total_strings = Translation.objects.filter(
                        resource = translation_resource,
                        language = translation_resource.source_language).count()

    translated_strings = Translation.objects.filter(
                            resource = translation_resource,
                            language = target_language).exclude(string="").count()

    return render_to_response("translate.html",
        { 'project' : translation_resource.project,
          'resource' : translation_resource,
          'target_language' : target_language,
          'translated_strings': translated_strings,
          'untranslated_strings': total_strings - translated_strings,
          'WEBTRANS_SUGGESTIONS': settings.WEBTRANS_SUGGESTIONS,
        },
        context_instance = RequestContext(request))


#FIXME: permissions needed
def view_strings(request, project_slug, resource_slug, lang_code,
                 *args, **kwargs):
    """
    View for observing the translations strings on a specific language.
    """

    translation_resource = Resource.objects.get(
        slug = resource_slug,
        project__slug = project_slug
    )
    target_language = Language.objects.by_code_or_alias(lang_code)

    total_strings = Translation.objects.filter(
                        resource = translation_resource,
                        language = translation_resource.source_language).count()

    translated_strings = Translation.objects.filter(
                            resource = translation_resource,
                            language = target_language).exclude(string="").count()

    return render_to_response("view_strings.html",
        { 'project' : translation_resource.project,
          'resource' : translation_resource,
          'target_language' : target_language,
          'translated_strings': translated_strings,
          'untranslated_strings': total_strings - translated_strings,
        },
        context_instance = RequestContext(request))


#FIXME: Find a more clever way to do it, to avoid putting placeholders.
SORTING_DICT=( 'id', 'id', 'string')

#FIXME: permissions needed
def stringset_handling(request, project_slug, resource_slug, lang_code,
                     *args, **kwargs):
    """
    Function to serve AJAX data to the datatable holding the translating
    stringset.
    """

#    if settings.DEBUG:
#       print 'iDisplayStart: %s' % request.POST.get('iDisplayStart','')
#       print 'iDisplayLength: %s' % request.POST.get('iDisplayLength','')
#       print 'sSearch: "%s"' % request.POST.get('sSearch','')
#       print 'bEscapeRegex: %s' % request.POST.get('bEscapeRegex','')
#       print 'iColumns: %s' % request.POST.get('iColumns','')
#       print 'iSortingCols: %s' % request.POST.get('iSortingCols','')
#       print 'iSortCol_0: %s' % request.POST.get('iSortCol_0','')
#       print 'sSortDir_0: %s' % request.POST.get('sSortDir_0','')
#       print 'iSortCol_1: %s' % request.POST.get('iSortCol_1','')
#       print 'sSortDir_1: %s' % request.POST.get('sSortDir_1','')
#       print 'sEcho: %s' % request.POST.get('sEcho','')

    try:
        resource = Resource.objects.get(slug=resource_slug,
                                project__slug = project_slug)
    except Resource.DoesNotExist:
        raise Http404

    source_strings = Translation.objects.filter(resource = resource,
                                language = resource.source_language)

    translated_strings = Translation.objects.filter(resource = resource,
                                language__code = lang_code)

    # status filtering (translated/untranslated)
    # TODO
    if request.POST and request.POST.has_key('filters'):
        for f in request.POST['filters'].split('&'):
            if f == "translated":
                source_strings = source_strings.filter(
                    Q(source_entity__id__in=translated_strings.filter(string="").values('source_entity'))|
                    ~Q(source_entity__id__in=translated_strings.values('source_entity')))
            if f == "untranslated":
                source_strings = source_strings.exclude(
                    Q(source_entity__id__in=translated_strings.filter(string="").values('source_entity'))|
                    ~Q(source_entity__id__in=translated_strings.values('source_entity')))

    # keyword filtering
    sSearch = request.POST.get('sSearch','')
    if not sSearch == '':
        query = Q()
        for term in sSearch.split(' '):
            query &= Q(string__icontains=term)
        source_strings = source_strings.filter(query)

    # grouping
    # TODO
    source_strings.group_by = ['string']

    # sorting
    scols = request.POST.get('iSortingCols', '0')
    for i in range(0,int(scols)):
        if request.POST.has_key('iSortCol_'+str(i)):
            col = int(request.POST.get('iSortCol_'+str(i)))
            if request.POST.has_key('sSortDir_'+str(i)) and \
                request.POST['sSortDir_'+str(i)] == 'asc':
                source_strings=source_strings.order_by(SORTING_DICT[col])
            else:
                source_strings=source_strings.order_by(SORTING_DICT[col]).reverse()

    # for items displayed
    dlength = int(request.POST.get('iDisplayLength','10'))
    dstart = int(request.POST.get('iDisplayStart','0'))
    # for statistics
    total = source_strings.count()

    # NOTE: It's important to keep the translation string matching inside this
    # iteration to prevent extra un-needed queries. In this iteration only the
    # strings displayed are calculated, saving a lot of resources.
    json = simplejson.dumps({
        'sEcho': request.POST.get('sEcho','1'),
        'iTotalRecords': total,
        'iTotalDisplayRecords': total,
        'aaData': [
            [
                s.id,
                s.source_entity.string,
                s.string,
                _get_string(translated_strings, source_entity = s.source_entity),
                # save buttons and hidden context
                ('<span class="i16 save buttonized_simple" id="save_' + str(counter) + '" style="display:none;border:0" title="Save the specific change"></span>'
                 '<span class="i16 undo buttonized_simple" id="undo_' + str(counter) + '" style="display:none;border:0" title="Undo to initial text"></span>'
                 '<span class="context" id="context_' + str(counter) + '" style="display:none;">' + str(s.source_entity.context) + '</span>'
                 '<span class="source_id" id="sourceid_' + str(counter) + '"style="display:none;">' + str(s.source_entity.id) + '</span>'),
            ] for counter,s in enumerate(source_strings[dstart:dstart+dlength])
        ],
        })

    return HttpResponse(json, mimetype='application/json')


def _get_string(query, **kwargs):
    """
    Helper function for returning a Translation string or an empty string if no
    translation is found. Used in the list concatenation above to preserve code
    sanity.
    """
    try:
        return query.get(**kwargs).string
    except:
        return ""


#FIXME: permissions needed
@login_required
def push_translation(request, project_slug, resource_slug, lang_code,
                                  *args, **kwargs):
    """
    Client pushes an id and a translation string.

    Id is considered to be of the source translation string and the string is
    in the target_lang.
    """
    
    if not request.POST:
        return HttpResponseBadRequest()

    data = json.loads(request.raw_post_data)
    strings = data["strings"]

    try:
        translation_resource = Resource.objects.get(
            slug = resource_slug,
            project__slug = project_slug
        )
    except Resource.DoesNotExist:
        raise Http404

    try:
        target_language = Language.objects.by_code_or_alias(lang_code)
    except Language.DoesNotExist:
        raise Http404

    # Form the strings dictionary, get as Json object
    # The fields are the following:
    # id-> source_entity id
    # translation-> translation string
    # context-> source_entity context
    # occurrence-> occurrence (not yet well supported)
    # Iterate through all the row data that have been sent.
    for row in strings:
        try:
            source_string = Translation.objects.get(id=row['id'])
        except Translation.DoesNotExist:
            # TODO: Log or inform here
            # If the source_string cannot be identified in the DB then go to next
            # translation pair.
            continue

        try:
            # TODO: Implement get based on context and/or on context too!
            translation_string, created = Translation.objects.get_or_create(
                                source_entity =source_string.source_entity,
                                language = target_language,
                                resource = translation_resource)

            translation_string.string = row['translation']
            # Save the sender as last committer for the translation.
            translation_string.user = request.user
            translation_string.save()
        # catch-all. if we don't save we _MUST_ inform the user
        except:
            # TODO: Log or inform here
            pass

    return HttpResponse(status=200)


#FIXME: permissions needed
@login_required
def resource_translations_delete(request, project_slug, resource_slug, lang_code):
    """
    Delete the set of Translation objects for a specific Language in a Resource.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                 slug = resource_slug)

    language = get_object_or_404(Language, code=lang_code)

    # Use a flag to denote if there is an attempt to delete the source language.
    is_source_language = False
    if resource.source_language == language:
        is_source_language = True

    if request.method == 'POST':
        Translation.objects.filter(resource=resource, language=language).delete()

        request.user.message_set.create(
            message=_("The translations of %s language for the %s resource were "
                      "deleted successfully.") % (language.name, resource.name))

        #TODO: Create the specific notice type and update all the other actions.

        return HttpResponseRedirect(reverse('resource_detail', 
                                    args=[resource.project.slug, resource.slug]),)
    else:
        return render_to_response(
            'resource_translations_confirm_delete.html',
            {'resource': resource,
             'language': language,
             'is_source_language': is_source_language},
            context_instance=RequestContext(request))


#FIXME: permissions needed
def get_details(request, project_slug=None, resource_slug=None, lang_code=None):
    """
    Ajax view that returns a template snippet for translation details.
    """

    if not request.POST and request.POST.has_key('source_id'):
        return HttpResponseBadRequest()

    resource = get_object_or_404(Resource, project__slug = project_slug,
                                 slug = resource_slug)
    target_language = get_object_or_404(Language, code=lang_code)
    project = resource.project
    source_entity = get_object_or_404(SourceEntity, pk=request.POST['source_id'])

    return render_to_response("lotte_details.html",
    { 'key': source_entity.string,
      'context': source_entity.context,
      'occurrences': source_entity.occurrences },
    context_instance = RequestContext(request))
