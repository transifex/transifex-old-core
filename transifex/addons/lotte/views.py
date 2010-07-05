# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import (HttpResponseRedirect, HttpResponse, Http404, 
                         HttpResponseForbidden, HttpResponseBadRequest)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from actionlog.models import action_logging
from happix.models import (Translation, Resource, SourceEntity)
from languages.models import Language
from projects.models import Project
from projects.permissions import *
from projects.permissions.project import ProjectPermission
from teams.models import Team
from txcommon.decorators import one_perm_required_or_403
from authority.views import permission_denied

try:
    import json
except:
    import simplejson as json

# Restrict access only to : (The checks are done in the view's body)
# 1)those belonging to the specific language team (coordinators or members)
# 2)project maintainers
# 3)global submitters (perms given through access control tab)
# 4)superusers
@login_required
def translate(request, project_slug, lang_code, resource_slug=None,
                     *args, **kwargs):
    """
    Main lotte view.
    """

    # Permissions handling
    # Project should always be available
    project = get_object_or_404(Project, slug=project_slug)
    team = Team.objects.get_or_none(project, lang_code)
    check = ProjectPermission(request.user)
    if not check.submit_file(team or project):
        return permission_denied(request)

    resources = []
    if resource_slug:
        try:
            resources = [ Resource.objects.get(
                slug = resource_slug,
                project = project
            ) ]
        except Resource.DoesNotExist:
            raise Http404
    else:
        resources = Resource.objects.filter(project = project)

        # Return a page explaining that the project has multiple source langs and
        # cannot be translated as a whole.
        if resources.values('source_language').distinct().count() > 1:
            request.user.message_set.create(
                message=_("This project has more than one source languages and as a "
                          "result you can not translate all resources at the "
                          "same time."))

            return HttpResponseRedirect(reverse('project_detail',
                                        args=[project_slug]),)

    target_language = Language.objects.by_code_or_alias(lang_code)

    total_strings = SourceEntity.objects.filter(
        resource__in = resources).count()

    translated_strings = Translation.objects.filter(
        resource__in = resources,
        language = target_language,
        rule = 5).exclude(string="").count()

    if len(resources) > 1:
        translation_resource = None
    else:
        translation_resource = resources[0]

    return render_to_response("translate.html",
        { 'project' : project,
          'resource' : translation_resource,
          'target_language' : target_language,
          'translated_strings': translated_strings,
          'untranslated_strings': total_strings - translated_strings,
          'WEBTRANS_SUGGESTIONS': settings.WEBTRANS_SUGGESTIONS,
        },
        context_instance = RequestContext(request))


# Restrict access only for private projects 
# Allow even anonymous access on public projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def view_strings(request, project_slug, lang_code, resource_slug=None,
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
                        language = translation_resource.source_language,
                        rule = 5).count()

    translated_strings = Translation.objects.filter(
                            resource = translation_resource,
                            language = target_language,
                            rule = 5).exclude(string="").count()

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

# Restrict access only for private projects since this is used to fetch stuff!
# Allow even anonymous access on public projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def stringset_handling(request, project_slug, lang_code, resource_slug=None,
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

    resources = []
    if resource_slug:
        try:
            resources = [ Resource.objects.get(slug=resource_slug,
                                    project__slug = project_slug) ]
        except Resource.DoesNotExist:
            raise Http404
    else:
        resources = Resource.objects.filter(project__slug = project_slug)

    # Find a way to determine the source language of multiple resources #FIXME
    source_strings = Translation.objects.filter(resource__in = resources,
                                language = resources[0].source_language,
                                rule=5)

    translated_strings = Translation.objects.filter(resource__in = resources,
                                language__code = lang_code,
                                rule=5)

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


# Restrict access only to : (The checks are done in the view's body)
# 1)those belonging to the specific language team (coordinators or members)
# 2)project maintainers
# 3)global submitters (perms given through access control tab)
# 4)superusers  
# CAUTION!!! WE RETURN 404 instead of 403 for security reasons
@login_required
def push_translation(request, project_slug, lang_code, resource_slug=None,
                                  *args, **kwargs):
    """
    Client pushes an id and a translation string.

    Id is considered to be of the source translation string and the string is
    in the target_lang.
    """

    # Permissions handling
    # Project should always be available
    project = get_object_or_404(Project, slug=project_slug)
    team = Team.objects.get_or_none(project, lang_code)
    check = ProjectPermission(request.user)
    if not check.submit_file(team or project):
        return permission_denied(request)

    if not request.POST:
        return HttpResponseBadRequest()

    data = json.loads(request.raw_post_data)
    strings = data["strings"]

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
            source_string = Translation.objects.get(id=int(row['id']))
        except Translation.DoesNotExist:
            # TODO: Log or inform here
            # If the source_string cannot be identified in the DB then go to next
            # translation pair.
            continue

        try:
            # TODO: Implement get based on context and/or on context too!
            # FIXME: Handle the plurals appropriately!
            translation_string, created = Translation.objects.get_or_create(
                                source_entity =source_string.source_entity,
                                language = target_language,
                                resource = source_string.resource)

            translation_string.string = row['translation']
            # Save the sender as last committer for the translation.
            translation_string.user = request.user
            translation_string.save()
        # catch-all. if we don't save we _MUST_ inform the user
        except:
            # TODO: Log or inform here
            pass

    return HttpResponse(status=200)

# Restrict access only for private projects since this is used to fetch stuff!
# Allow even anonymous access on public projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def get_details(request, project_slug=None, resource_slug=None, lang_code=None):
    """
    Ajax view that returns a template snippet for translation details.
    """

    if not request.POST and request.POST.has_key('source_id'):
        return HttpResponseBadRequest()

    source_entity = get_object_or_404(SourceEntity, pk=request.POST['source_id'])

    last_translations = Translation.objects.filter(source_entity=source_entity,
        language__code=lang_code).order_by('-last_update')
    last_translation = None
    if last_translations:
        last_translation = last_translations[0]

    return render_to_response("lotte_details.html",
    { 'key': source_entity.string,
      'context': source_entity.context,
      'occurrences': source_entity.occurrences,
      'last_translation': last_translation },
    context_instance = RequestContext(request))
