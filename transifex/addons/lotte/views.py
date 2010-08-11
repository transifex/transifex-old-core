# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.db.models.loading import get_model
from django.http import (HttpResponseRedirect, HttpResponse, Http404, 
                         HttpResponseForbidden, HttpResponseBadRequest)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils.html import escape
from authority.views import permission_denied

from actionlog.models import action_logging
from languages.models import Language
from projects.models import Project
from projects.permissions import *
from projects.permissions.project import ProjectPermission
from resources.models import (Translation, Resource, SourceEntity)
from teams.models import Team
from txcommon.decorators import one_perm_required_or_403

# Temporary
from txcommon import notifications as txnotification

Suggestion = get_model('suggestions', 'Suggestion')

from signals import lotte_init, lotte_done

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

    target_language = Language.objects.by_code_or_alias_or_404(lang_code)

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

    contributors = User.objects.filter(pk__in=Translation.objects.filter(
        resource__in = resources,
        language = target_language,
        rule = 5).values_list("user", flat=True))

    lotte_init.send(None, request=request, resources=resources,
        language=target_language)

    return render_to_response("translate.html",
        { 'project' : project,
          'resource' : translation_resource,
          'target_language' : target_language,
          'translated_strings': translated_strings,
          'untranslated_strings': total_strings - translated_strings,
          'WEBTRANS_SUGGESTIONS': settings.WEBTRANS_SUGGESTIONS,
          'contributors': contributors,
          'resources': resources,
          'resource_slug': resource_slug,
          'languages': Language.objects.all()
        },
        context_instance = RequestContext(request))

@login_required
def exit(request, project_slug, lang_code, resource_slug=None, *args, **kwargs):
    """
    Exiting Lotte
    """

    # Permissions handling
    # Project should always be available
    project = get_object_or_404(Project, slug=project_slug)
    team = Team.objects.get_or_none(project, lang_code)
    check = ProjectPermission(request.user)
    if not check.submit_file(team or project):
        return permission_denied(request)

    language = Language.objects.by_code_or_alias(lang_code)

    resources = []
    if resource_slug:
        resources = Resource.objects.filter(slug=resource_slug, project=project)
        if not resources:
            raise Http404
        url = reverse('resource_detail', args=[project_slug, resource_slug])
    else:
        resources = Resource.objects.filter(project=project)
        url = reverse('project_detail', args=[project_slug])

    if request.POST.get('updated', None) == 'true':
        modified = True
        # ActionLog & Notification
        for resource in resources:
            nt = 'project_resource_translated'
            context = {'project': project,
                       'resource': resource,
                       'language': language}
            object_list = [project, resource, language]
            action_logging(request.user, object_list, nt, context=context)
            if settings.ENABLE_NOTICES:
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
    else:
        modified = False

    lotte_done.send(None, request=request, resources=resources,
        language=language, modified=modified)

    if request.is_ajax():
        json = simplejson.dumps(dict(redirect=url))
        return HttpResponse(json, mimetype='application/json')

    return HttpResponseRedirect(url)


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
    source_language = resources[0].source_language
    source_strings = Translation.objects.filter(resource__in = resources,
                                language = source_language,
                                rule=5)

    translated_strings = Translation.objects.filter(resource__in = resources,
                                language__code = lang_code)

    # These are only the rule=5 (other) translations
    default_translated_strings = translated_strings.filter(rule=5)

    # status filtering (translated/untranslated)
    if request.POST and request.POST.has_key('filters'):
        for f in request.POST['filters'].split(','):
            if f == "translated":
                source_strings = source_strings.filter(
                    Q(source_entity__id__in=default_translated_strings.filter(
                        string="").values('source_entity'))|
                    ~Q(source_entity__id__in=default_translated_strings.values(
                        'source_entity')))
            elif f == "untranslated":
                source_strings = source_strings.exclude(
                    Q(source_entity__id__in=default_translated_strings.filter(
                        string="").values('source_entity'))|
                    ~Q(source_entity__id__in=default_translated_strings.values(
                        'source_entity')))

    # Object filtering (e.g. users, resources etc.)
    if request.POST and request.POST.has_key('user_filters'):
        # rsplit is used to remove the trailing ','
        users = request.POST.get('user_filters').rstrip(',').split(',')
        source_strings = source_strings.filter(
            source_entity__id__in=default_translated_strings.filter(
                user__id__in=users).values('source_entity'))
    if request.POST and request.POST.has_key('resource_filters'):
        # rsplit is used to remove the trailing ','
        resources = request.POST.get('resource_filters').rstrip(',').split(',')
        source_strings = source_strings.filter(resource__id__in=resources)

    more_languages = []
    if request.POST and request.POST.has_key('more_languages'):
        # rsplit is used to remove the trailing ','
        more_languages = request.POST.get('more_languages').rstrip(',').split(',')


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
                _get_source_strings(s, source_language, lang_code, more_languages),
                _get_strings(translated_strings, lang_code, s.source_entity),
                Suggestion.objects.filter(source_entity=s.source_entity, language__code=lang_code).count(),
                # save buttons and hidden context
                ('<span class="i16 save buttonized_simple" id="save_' + str(counter) + '" style="display:none;border:0" title="Save the specific change"></span>'
                 '<span class="i16 undo buttonized_simple" id="undo_' + str(counter) + '" style="display:none;border:0" title="Undo to initial text"></span>'
                 '<span class="context" id="context_' + str(counter) + '" style="display:none;">' + escape(str(s.source_entity.context)) + '</span>'
                 '<span class="source_id" id="sourceid_' + str(counter) + '"style="display:none;">' + str(s.source_entity.id) + '</span>'),
            ] for counter,s in enumerate(source_strings[dstart:dstart+dlength])
        ],
        })
    return HttpResponse(json, mimetype='application/json')


def _get_source_strings(source_string, source_language, lang_code, more_languages):
    """
    Get all the necessary source strings, including plurals and similar langs.
    
    Returns a dictionary with the keys:
    'source_strings' : {"one":<string>, "two":<string>, ... , "other":<string>}
    'similar_lang_strings' : 
        {"lang1": {"one":<string>, ... , "other":<string>},
         "lang2": {"one":<string>, "two":<string>, ... , "other":<string>}}
    """
    source_entity = source_string.source_entity
    # This is the rule 5 ('other')
    source_strings = { "other":source_string.string }
    # List that will contain all the similar translations
    similar_lang_strings = {}
    
    if source_entity.pluralized:
        # These are the remaining plural forms of the source string.
        plural_strings = Translation.objects.filter(
            source_entity = source_entity,
            language = source_language).exclude(rule=5).order_by('rule')
        for pl_string in plural_strings:
            plural_name = source_language.get_rule_name_from_num(pl_string.rule)
            source_strings[plural_name] = pl_string.string

    # for each similar language fetch all the translation strings
    for lang_id in more_languages:
        l = Language.objects.get(pk=lang_id)
        similar_lang_strings[l.name] = {}
        for t in Translation.objects.filter(source_entity=source_entity, language=l).order_by('rule'):
            plural_name = source_language.get_rule_name_from_num(t.rule)
            similar_lang_strings[l.name][plural_name] = t.string
    return { 'source_strings' : source_strings,
             'similar_lang_strings' : similar_lang_strings }


def _get_strings(query, target_lang_code, source_entity):
    """
    Helper function for returning all the Translation strings or an empty dict.
    
    Used in the list concatenation above to preserve code sanity.
    Returns a dictionary in the following form:
    {"zero":<string>, "one":<string>, ... , "other":<string>},
    where the 'zero', 'one', ... are the plural names of the corresponding 
    plural forms.
    """
    # It includes the plural translations, too!
    translation_strings = {}
    target_language = Language.objects.by_code_or_alias(target_lang_code)
    if source_entity.pluralized:
        translations = query.filter(source_entity=source_entity).order_by('rule')
        # Fill with empty strings to have the UNtranslated entries!
        for rule in target_language.get_pluralrules():
            translation_strings[rule] = ""
        for translation in translations:
            plural_name = target_language.get_rule_name_from_num(translation.rule)
            translation_strings[plural_name] = translation.string
    else:
        try:
            translation_strings["other"] = query.get(source_entity=source_entity,
                                                     rule=5).string
        except Translation.DoesNotExist:
            translation_strings["other"] = ""
    return translation_strings


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
    # translations-> translation strings (includes all plurals)
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

        for rule, string in row['translations'].items():
            try:
                # TODO: Implement get based on context and/or on context too!
                translation_string = Translation.objects.get(
                    source_entity = source_string.source_entity,
                    language = target_language,
                    resource = source_string.resource,
                    rule = target_language.get_rule_num_from_name(rule))

                # FIXME: Maybe we don't want to permit anyone to delete!!!
                # If an empty string has been issued then we delete the translation.
                if string == "":
                    translation_string.delete()
                else:
                    translation_string.string = string
                    translation_string.user = request.user
                    translation_string.save()
            except Translation.DoesNotExist:
                # Only create new if the translation string sent, is not empty!
                if string != "":
                    Translation.objects.create(
                        source_entity = source_string.source_entity,
                        language = target_language,
                        resource = source_string.resource,
                        rule = target_language.get_rule_num_from_name(rule),
                        string = string,
                        user = request.user) # Save the sender as last committer
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

# Restrict access only to :
# 1)project maintainers
# 2)superusers
@one_perm_required_or_403(pr_resource_translations_delete,
                          (Project, "slug__exact", "project_slug"))
def delete_translation(request, project_slug=None, resource_slug=None,
                        lang_code=None):
    """
    Delete a list of translations according to the post request.
    """

    if not request.POST and request.POST.has_key('to_delete'):
        return HttpResponseBadRequest()

    data = json.loads(request.raw_post_data)
    to_delete = data["to_delete"]

    ids = []
    # Ensure that there are no empty '' ids
    for se_id in to_delete:
        if se_id:
            ids.append(se_id)

    try:
        Translation.objects.filter(source_entity__pk__in=ids,
                                   language__code=lang_code).delete();
#        request.user.message_set.create(
#            message=_("Translations deleted successfully!"))
    except:
#        request.user.message_set.create(
#            message=_("Translations did not delete due to some error!"))
        raise Http404

    return HttpResponse(status=200)
