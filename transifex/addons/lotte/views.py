# -*- coding: utf-8 -*-
from datetime import date
import re
from polib import escape, unescape
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.loading import get_model
from django.http import (HttpResponseRedirect, HttpResponse, Http404,
                         HttpResponseForbidden, HttpResponseBadRequest)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils.html import escape
from django.views.generic import list_detail
from authority.views import permission_denied

from actionlog.models import action_logging
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.projects.permissions import *
from transifex.projects.permissions.project import ProjectPermission
from transifex.resources.models import (Translation, Resource, SourceEntity)
from transifex.resources.handlers import invalidate_stats_cache
from transifex.teams.models import Team
from transifex.txcommon.decorators import one_perm_required_or_403

# Temporary
from transifex.txcommon import notifications as txnotification

from transifex.addons.gtranslate.models import Gtranslate

Suggestion = get_model('suggestions', 'Suggestion')

from signals import lotte_init, lotte_done, lotte_save_translation

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
    if not check.submit_translations(team or project) and not\
        check.maintain(project):
        return permission_denied(request)

    resources = []
    if resource_slug:
        resource_list = [get_object_or_404(Resource, slug=resource_slug,
            project=project)]
    else:
        resource_list = Resource.objects.filter(project=project)

        # Return a page explaining that the project has multiple source langs and
        # cannot be translated as a whole.
        if resource_list.values('source_language').distinct().count() > 1:
            messages.info(request,
                          "There are multiple source languages for this project. "
                          "You will only be able to translate resources for one "
                          "source language at a time.")
            return HttpResponseRedirect(reverse('project_detail',
                                        args=[project_slug]),)

    # Filter resources that are not accepting translations
    for resource in resource_list:
        if resource.accept_translations:
            resources.append(resource)

    # If no resource accepting translations, raise a 403
    if not resources:
        return permission_denied(request)

    target_language = Language.objects.by_code_or_alias_or_404(lang_code)

    # If it is an attempt to edit the source language, redirect the user to
    # resource_detail and show him a message explaining the reason.
    if target_language == resources[0].source_language:
        messages.error(request,
                       "Cannot edit the source language because this would "
                       "result in translation mismatches! If you want to "
                       "update the source strings consider using the transifex "
                       "command-line client.")
        if resource_slug:
            return HttpResponseRedirect(reverse('resource_detail',
                                                args=[project_slug,
                                                      resource_slug]),)
        else:
            return HttpResponseRedirect(reverse('project_detail',
                                                args=[project_slug]),)

    total_strings = SourceEntity.objects.filter(
        resource__in = resources).count()

    translated_strings = Translation.objects.filter(
        source_entity__resource__in = resources,
        language = target_language,
        source_entity__pluralized=False,
        rule = 5).exclude(string="").count()

    # Include counting of pluralized entities
    for pluralized_entity in SourceEntity.objects.filter(resource__in = resources,
                                                         pluralized=True):
        plurals_translated = Translation.objects.filter(
            language=target_language,
            source_entity=pluralized_entity).count()
        if plurals_translated == len(target_language.get_pluralrules()):
            translated_strings += 1

    if len(resources) > 1:
        translation_resource = None
    else:
        translation_resource = resources[0]

    contributors = User.objects.filter(pk__in=Translation.objects.filter(
        source_entity__resource__in = resources,
        language = target_language,
        rule = 5).values_list("user", flat=True))

    lotte_init.send(None, request=request, resources=resources,
        language=target_language)

    use_gtranslate = True
    try:
        use_gtranslate = Gtranslate.objects.get(project=project).use_gtranslate
    except Gtranslate.DoesNotExist:
        pass
    return render_to_response("translate.html",
        { 'project' : project,
          'resource' : translation_resource,
          'target_language' : target_language,
          'translated_strings': translated_strings,
          'untranslated_strings': total_strings - translated_strings,
          'contributors': contributors,
          'resources': resources,
          'resource_slug': resource_slug,
          'languages': Language.objects.all(),
          'gtranslate': use_gtranslate
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
    if not check.submit_translations(team or project) and not\
        check.maintain(project):
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

    translation_resource = get_object_or_404(Resource,
        slug = resource_slug,
        project__slug = project_slug
    )
    try:
        target_language = Language.objects.by_code_or_alias(lang_code)
    except Language.DoesNotExist:
        raise Http404

    total_strings = Translation.objects.filter(
                        source_entity__resource = translation_resource,
                        language = translation_resource.source_language,
                        rule = 5).count()

    translated_strings = Translation.objects.filter(
                            source_entity__resource = translation_resource,
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
    source_strings = Translation.objects.filter(
        source_entity__resource__in=resources,
        language=source_language,
        rule=5)

    translated_strings = Translation.objects.filter(
        source_entity__resource__in=resources,
        language__code=lang_code)

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

    # Object filtering (e.g. users, resources, etc.)
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
    dlength = int(request.POST.get('iDisplayLength','25'))
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
                # 1. Translation object's "id"
                s.id,
                # 2. SourceEntity object's "string" content
                s.source_entity.string,
                # 3. Get all the necessary source strings, including plurals and
                # similar langs, all in a dictionary (see also below)
                _get_source_strings(s, source_language, lang_code, more_languages),
                # 4. Get all the Translation strings mapped with plural rules
                # in a single dictionary (see docstring of function)
                _get_strings(translated_strings, lang_code, s.source_entity),
                # 5. A number which indicates the number of Suggestion objects
                # attached to this row of the table.
                Suggestion.objects.filter(source_entity=s.source_entity, language__code=lang_code).count(),
                # 6. save buttons and hidden context (ready to inject snippet)
                # It includes the following content, wrapped in span tags:
                # * SourceEntity object's "context" value
                # * SourceEntity object's "id" value
                ('<span class="i16 save buttonized_simple" id="save_' + str(counter) + '" style="display:none;border:0" title="' + _("Save the specific change") + '"></span>'
                 '<span class="i16 undo buttonized_simple" id="undo_' + str(counter) + '" style="display:none;border:0" title="' + _("Undo to initial text") + '"></span>'
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
        # Fill with empty strings to have the Untranslated entries!
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
def push_translation(request, project_slug, lang_code, *args, **kwargs):
    """
    Client pushes an id and a translation string.

    Id is considered to be of the source translation string and the string is
    in the target_lang.

    FIXME: Document in detail the form of the 'strings' POST variable.
    """

    # Permissions handling
    # Project should always be available
    project = get_object_or_404(Project, slug=project_slug)
    team = Team.objects.get_or_none(project, lang_code)
    check = ProjectPermission(request.user)
    if not check.submit_translations(team or project) and not\
        check.maintain(project):
        return permission_denied(request)

    if not request.POST:
        return HttpResponseBadRequest()

    data = simplejson.loads(request.raw_post_data)
    strings = data["strings"]

    try:
        target_language = Language.objects.by_code_or_alias(lang_code)
    except Language.DoesNotExist:
        raise Http404

    # This dictionary will hold the results of the save operation and will map
    # status code for each translation pushed, to indicate the result on each
    # translation push separately.
    push_response_dict = {}

    # Form the strings dictionary, get as Json object
    # The fields are the following:
    # id-> source_entity id
    # translations-> translation strings (includes all plurals)
    # context-> source_entity context
    # occurrence-> occurrence (not yet well supported)
    # Iterate through all the row data that have been sent.
    for row in strings:
        source_id = int(row['id'])
        try:
            source_string = Translation.objects.get(id=source_id,
                source_entity__resource__project=project)
        except Translation.DoesNotExist:
            # TODO: Log or inform here
            push_response_dict[source_id] = { 'status':500,
                 'message':_("Source string cannot be identified in the DB")}
            # If the source_string cannot be identified in the DB then go to next
            # translation pair.
            continue

        if not source_string.source_entity.resource.accept_translations:
            push_response_dict[source_id] = { 'status':500,
                 'message':_("The resource of this source string is not "
                    "accepting translations.") }

        # If the translated source string is pluralized check that all the
        # source language supported rules have been filled in, else return error
        # and donot save the translations.
        if source_string.source_entity.pluralized:
            error_flag = False
            for rule in target_language.get_pluralrules():
                if rule in row['translations'] and row['translations'][rule] != "":
                    continue
                else:
                    error_flag = True
            if error_flag:
                error_flag = False
                # Check also if all of them are "". If yes, delete all the plurals!
                for rule in target_language.get_pluralrules():
                    if rule in row['translations'] and row['translations'][rule] == "":
                        continue
                    else:
                        error_flag = True
            if error_flag:
                push_response_dict[source_id] = { 'status':500,
                    'message':(_("Cannot save unless plural translations are either "
                               "completely specified or entirely empty!"))}
                # Skip the save as we hit on an error.
                continue

        for rule, string in row['translations'].items():
            # Check for plural entries if we already have an error for one of
            # the plural forms
            if push_response_dict.has_key(source_id) and\
              push_response_dict[source_id]['status'] == 500:
                continue

            source_language = source_string.source_entity.resource.source_language
            if rule == "other":
                ss = unescape(source_string.string)
            else:
                try:
                    source_string = Translation.objects.get(source_entity=
                        source_string.source_entity,
                        language = source_language,
                        rule = source_language.get_rule_num_from_name(rule))
                except Translation.DoesNotExist:
                    # This shouldn't happen
                    pass
                finally:
                    ss = unescape(source_string.string)
            tr = unescape(string)

                    # Check whether the translation sting only contains spaces
            if tr and len(tr.strip()) == 0:
                push_response_dict[source_id] = { 'status':200,
                    'message':_("Translation string only contains whitespaces.")}

            # Test that the number of {[()]} appearing in each string are the
            # same
            try:
                for char in '[{()}]':
                    if tr and ss.count(char) != tr.count(char):
                        push_response_dict[source_id] = { 'status':200,
                        'message':_("Translation string doesn't contain the same"
                        " number of '%s' as the source string." % char )}
                        raise StopIteration
            except StopIteration:
                pass
            # Scan for urls and see if they're in both strings
            urls = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
            try:
                for url in urls.findall(ss):
                    if tr and url not in tr:
                        push_response_dict[source_id] = { 'status':200,
                        'message':_("The following url is either missing from the"
                        " translation or has been translated: '%s'." % url)}
                        raise StopIteration
            except StopIteration:
                pass

            # Scan for urls and see if they're in both strings
            emails = re.compile("([\w\-\.+]+@[\w\w\-]+\.+[\w\-]+)")
            try:
                for email in emails.findall(ss):
                    if tr and email not in tr:
                        push_response_dict[source_id] = { 'status':200,
                        'message':_("The following email is either missing from the"
                        " translation or has been translated: '%s'." % email)}
                        raise StopIteration
            except StopIteration:
                pass

            # Check whether source string and translation start and end
            # with newlines
            if string and ss.startswith('\n') != tr.startswith('\n'):
                if ss.startswith('\n'):
                    push_response_dict[source_id] = { 'status':200,
                    'message':_("Translation must start with a newline (\\n)")}
                else:
                    push_response_dict[source_id] = { 'status':200,
                    'message':_("Translation should not start with a newline (\\n)")}
                pass
            elif string and ss.endswith('\n') != tr.endswith('\n'):
                if ss.endswith('\n'):
                    push_response_dict[source_id] = { 'status':200,
                    'message':_("Translation must end with a newline (\\n)")}
                else:
                    push_response_dict[source_id] = { 'status':200,
                    'message':_("Translation should not end with a newline (\\n)")}
                pass

            # Check the numbers inside the string
            numbers = re.compile("[-+]?[0-9]*\.?[0-9]+")
            try:
                for num in numbers.findall(source_string.string):
                    if string and num not in string:
                        push_response_dict[source_id] = { 'status':200,
                            'message':_("Number %s is in the source string but not "\
                            "in the translation." % num )}
                        raise StopIteration
            except StopIteration:
                pass

            # Check printf variables
            printf_pattern = re.compile('%((?:(?P<ord>\d+)\$|\((?P<key>\w+)\))'\
                '?(?P<fullvar>[+#-]*(?:\d+)?(?:\.\d+)?(hh\|h\|l\|ll)?(?P<type>[\w%])))')
            ss_matches = list(printf_pattern.finditer(source_string.string))
            tr_matches = list(printf_pattern.finditer(string))
            # Since this doesn't allow translations to be saved, we'll only
            # check it if the number of plurals of the source language and the
            # target language is the same.
            if target_language.nplurals == source_language.nplurals:
                # Check number of printf variables
                if string and len(printf_pattern.findall(source_string.string)) != \
                    len(printf_pattern.findall(string)):
                    push_response_dict[source_id] = { 'status':500,
                        'message':_('The number of arguments seems to differ '
                            'between the source string and the translation.')}
                    continue

            try:
                for pattern in ss_matches:
                    if string and pattern.group(0) not in string:
                        push_response_dict[source_id] = { 'status':200,
                            'message':_('The expression \'%s\' is not present '\
                            'in the translation.' % pattern.group(0) )}
                        raise StopIteration
            except StopIteration:
                continue

            try:
                for pattern in tr_matches:
                    if string and pattern.group(0) not in source_string.string:
                        push_response_dict[source_id] = { 'status':200,
                            'message':_('The expression \'%s\' is not present '\
                            'in the source string.' % pattern.group(0) )}
            except StopIteration:
                pass


            try:
                # TODO: Implement get based on context and/or on context too!
                translation_string = Translation.objects.get(
                    source_entity = source_string.source_entity,
                    language = target_language,
                    source_entity__resource = source_string.source_entity.resource,
                    rule = target_language.get_rule_num_from_name(rule))

                # FIXME: Maybe we don't want to permit anyone to delete!!!
                # If an empty string has been issued then we delete the translation.
                if string == "":
                    translation_string.delete()
                else:
                    translation_string.string = string
                    translation_string.user = request.user
                    translation_string.save()

                # signal new translation
                from transifex.addons.copyright.handlers import save_copyrights
                lotte_save_translation.connect(save_copyrights)
                lotte_save_translation.send(
                    None, resource=source_string.source_entity.resource,
                    language=target_language,
                    copyrights=([(
                        ''.join([request.user.first_name, ' ', request.user.last_name,
                                 '<', request.user.email, '>']),
                        [str(date.today().year)]
                    ), ])
                )
                invalidate_stats_cache(source_string.source_entity.resource,
                    target_language, user=request.user)
                if not push_response_dict.has_key(source_id):
                    push_response_dict[source_id] = { 'status':200}
            except Translation.DoesNotExist:
                # Only create new if the translation string sent, is not empty!
                if string != "":
                    Translation.objects.create(
                        source_entity = source_string.source_entity,
                        language = target_language,
                        rule = target_language.get_rule_num_from_name(rule),
                        string = string,
                        user = request.user) # Save the sender as last committer
                    invalidate_stats_cache(source_string.source_entity.resource,
                        target_language, user=request.user)
                    if not push_response_dict.has_key(source_id):
                        push_response_dict[source_id] = { 'status':200}
                else:
                    # In cases of pluralized translations, sometimes only one
                    # translation will exist and the rest plural forms will be
                    # empty. If the user wants to delete all of them, we need
                    # to let by the ones that don't already have a translation.
                    if source_string.source_entity.pluralized:
                        if not push_response_dict.has_key(source_id):
                            push_response_dict[source_id] = { 'status':200}
                    else:
                        push_response_dict[source_id] = { 'status':500,
                             'message':_("The translation string is empty")}
            # catch-all. if we don't save we _MUST_ inform the user
            except:
                # TODO: Log or inform here
                push_response_dict[source_id] = { 'status':500,
                    'message':_("Error occurred while trying to save translation.")}

    json_dict = simplejson.dumps(push_response_dict)
    return HttpResponse(json_dict, mimetype='application/json')


# Restrict access only for private projects since this is used to fetch stuff
# Allow even anonymous access on public projects
def tab_details_snippet(request, entity_id, lang_code):
    """Return a template snippet with entity & translation details."""

    source_entity = get_object_or_404(SourceEntity, pk=entity_id)

    check = ProjectPermission(request.user)
    if not check.private(source_entity.resource.project):
        return permission_denied(request)

    language = get_object_or_404(Language, code=lang_code)
    translation = source_entity.get_translation(language.code)

    return list_detail.object_detail(request,
        queryset=SourceEntity.objects.all(),
        object_id=entity_id,
        template_name="tab_details_snippet.html",
        template_object_name='source_entity',
        extra_context={"translation" : translation})


# Restrict access only for private projects since this is used to fetch stuff
# Allow even anonymous access on public projects
def tab_suggestions_snippet(request, entity_id, lang_code):
    """Return a template snippet with entity & translation details."""

    source_entity = get_object_or_404(SourceEntity, pk=entity_id)

    check = ProjectPermission(request.user)
    if not check.private(source_entity.resource.project):
        return permission_denied(request)

    current_translation = source_entity.get_translation(lang_code)

    return render_to_response("tab_suggestions_snippet.html", {
        'source_entity': source_entity,
        'lang_code': lang_code,
        'current_translation': current_translation
        },
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

    if not request.POST:
        return HttpResponseBadRequest()

    project = get_object_or_404(Project, slug=project_slug)

    resource = get_object_or_404(Resource, slug=resource_slug, project=project)
    language = get_object_or_404(Language, code=lang_code)
    data = simplejson.loads(request.raw_post_data)
    to_delete = data["to_delete"]
    ids = []
    # Ensure that there are no empty '' ids
    for se_id in to_delete:
        if se_id:
            ids.append(se_id)


    try:
        translations = Translation.objects.filter(source_entity__pk__in=ids,
                                   language=language)

        translations.delete()
#        request.user.message_set.create(
#            message=_("Translations deleted successfully!"))
    except:
#        request.user.message_set.create(
#            message=_("Failed to delete translations due to some error!"))
        raise Http404

    invalidate_stats_cache(resource, language, user=request.user)

    return HttpResponse(status=200)
