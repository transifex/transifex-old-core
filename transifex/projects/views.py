# -*- coding: utf-8 -*-
import os
import re
import codecs

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader, Context
from django.dispatch import Signal
from django.views.generic import create_update, list_detail
from django.utils.translation import ugettext as _
from django.utils.datastructures import MultiValueDictKeyError
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.syndication.views import feed

from codebases.forms import UnitForm
from projects.models import Project, Component
from projects.forms import (ProjectAccessSubForm, ProjectForm, ComponentForm, 
                            ComponentAllowSubForm)
from projects import signals
from projects.permissions import ProjectPermission
from tarball.forms import TarballSubForm
from txcommon.log import logger
from actionlog.models import action_logging
from translations.lib.types.pot import FileFilterError
from translations.lib.types.publican import PotDirError
from translations.models import (POFile, POFileLock)
from languages.models import Language
from txcommon.decorators import perm_required_with_403, one_perm_required_or_403
from txcommon.forms import unit_sub_forms
from txcommon.models import exclusive_fields, get_profile_or_user
from txcommon.views import (json_result, json_error)
from repowatch import WatchException, watch_titles
from repowatch.models import Watch
from notification import models as notification
from vcs.forms import VcsUnitSubForm
from submissions import submit_by_email
from authority.models import Permission
from authority.views import permission_denied
from txpermissions.views import (add_permission_or_request,
                                 approve_permission_request,
                                 delete_permission_or_request)
# Temporary
from txcommon import notifications as txnotification

def _get_project_and_permission(project_slug, permission_pk):
    """
    Handler to return a project and a permission instance or a 404 error, based 
    on the slugs passed by parameter.
    """
    project = get_object_or_404(Project, slug=project_slug)
    ctype = ContentType.objects.get_for_model(Project)
    permission = get_object_or_404(Permission, object_id=project.pk, 
                                   content_type=ctype, id=permission_pk)
    return project, permission

# Feeds

def slug_feed(request, slug=None, param='', feed_dict=None):
    """
    Override default feed, using custom (including inexistent) slug.
    
    Provides the functionality needed to decouple the Feed's slug from
    the urlconf, so a feed mounted at "^/feed" can exist.
    
    See also http://code.djangoproject.com/ticket/6969.
    """
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)


# Projects


pr_project_add = (
    ('general',  'projects.add_project'),
)
@login_required
@one_perm_required_or_403(pr_project_add)
def project_create(request):
    return _project_create_update(request)


pr_project_add_change = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.change_project'),
)
@login_required
@one_perm_required_or_403(pr_project_add_change, 
    (Project, 'slug__exact', 'project_slug'))
def project_update(request, project_slug):
        return _project_create_update(request, project_slug)


def _project_create_update(request, project_slug=None):

    if project_slug:
        project = get_object_or_404(Project, slug=project_slug)
    else:
        project = None

    if request.method == 'POST':
        # Access Control tab
        if request.POST.has_key('access_control_form'):
            anyone_subform = ProjectAccessSubForm(request.POST, instance=project)
            if anyone_subform.is_valid():
                anyone_subform.save()
                # TODO: Add an ActionLog and Notification here for this action
                return HttpResponseRedirect(request.POST['next'])

        # Details tab
        else:
            project_form = ProjectForm(request.POST, instance=project, 
                                    prefix='project') 
            if project_form.is_valid(): 
                project = project_form.save(commit=False)
                project_id = project.id
                project.save()
                project_form.save_m2m()

                # TODO: Not sure if here is the best place to put it
                Signal.send(signals.post_proj_save_m2m, sender=Project, 
                            instance=project)

                # ActionLog & Notification
                context = {'project': project}
                if not project_id:
                    nt = 'project_added'
                    action_logging(request.user, [project], nt, context=context)
                else:
                    nt = 'project_changed'
                    action_logging(request.user, [project], nt, context=context)
                    if settings.ENABLE_NOTICES:
                        txnotification.send_observation_notices_for(project, 
                                            signal=nt, extra_context=context)

                return HttpResponseRedirect(reverse('project_detail',
                                            args=[project.slug]),)
    else:
        # Make the current user the maintainer when adding a project
        if project:
            initial_data = {}
        else:
            initial_data = {"maintainers": [request.user.pk]}

        project_form = ProjectForm(instance=project, prefix='project',
                                   initial=initial_data)

    return render_to_response('projects/project_form_base.html', {
        'project_form': project_form,
        'project': project,
    }, context_instance=RequestContext(request))


pr_project_delete = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.delete_project'),
)
@login_required
@one_perm_required_or_403(pr_project_delete, 
    (Project, 'slug__exact', 'project_slug'))
def project_delete(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if request.method == 'POST':
        import copy
        project_ = copy.copy(project)
        project.delete()

        request.user.message_set.create(
            message=_("The %s was deleted.") % project.name)

        # ActionLog & Notification
        nt = 'project_deleted'
        context={'project': project_}
        action_logging(request.user, [project_], nt, context=context)

        return HttpResponseRedirect(reverse('project_list'))
    else:
        return render_to_response(
            'projects/project_confirm_delete.html', {'project': project,},
            context_instance=RequestContext(request))


pr_project_add_perm = (
    ('granular', 'project_perm.maintain'),
    ('general',  'authority.add_permission'),
)
@login_required
@one_perm_required_or_403(pr_project_add_perm, 
    (Project, 'slug__exact', 'project_slug'))
def project_add_permission(request, project_slug):
    """
    Return a view with a form for adding a permission for an user.
    
    This view is an abstraction of a txpermissions.views method to be able to
    apply granular permission on it using a decorator. 
    """
    project = get_object_or_404(Project, slug=project_slug)
    return add_permission_or_request(request, project, 
        view_name='project_add_permission',
        approved=True,
        extra_context={
            'project_permission': True,
            'project': project,
            'project_form': ProjectAccessSubForm(instance=project),
        },
        template_name='projects/project_form_base.html')


@login_required
def project_add_permission_request(request, project_slug):
    """
    Return a view with a form for adding a request of permission for an user.

    This view is an abstraction of a txpermissions.views method. 
    """
    project = get_object_or_404(Project, slug=project_slug)
    return add_permission_or_request(request, project,
        view_name='project_add_permission_request',
        approved=False,
        extra_context={
            'project_permission': True,
            'project': project, 
            'project_form': ProjectAccessSubForm(instance=project),
        },
        template_name='projects/project_form_base.html')


pr_project_approve_perm = (
    ('granular', 'project_perm.maintain'),
    ('general',  'authority.approve_permission_requests'),
)
@login_required
@one_perm_required_or_403(pr_project_approve_perm, 
    (Project, 'slug__exact', 'project_slug'))
def project_approve_permission_request(request, project_slug, permission_pk):
    project, permission=_get_project_and_permission(project_slug, permission_pk)
    return approve_permission_request(request, permission)


pr_project_delete_perm = (
    ('granular', 'project_perm.maintain'),
    ('general',  'authority.delete_permission'),
)
@login_required
@one_perm_required_or_403(pr_project_delete_perm, 
    (Project, 'slug__exact', 'project_slug'))
def project_delete_permission(request, project_slug, permission_pk):
    """
    View for deleting a permission of an user.

    This view is an abstraction of a txpermissions.views method to be able to
    apply granular permission on it using a decorator. 
    """
    project, permission=_get_project_and_permission(project_slug, permission_pk)
    return delete_permission_or_request(request, permission, True)


@login_required
def project_delete_permission_request(request, project_slug, permission_pk):
    """
    View for deleting a request of permission of an user.

    This view is an abstraction of a txpermissions.views method. 
    """
    project, permission=_get_project_and_permission(project_slug, permission_pk)

    check = ProjectPermission(request.user)
    if check.maintain(project) or request.user.has_perm('authority.delete_permission') \
        or request.user.pk == permission.creator.pk:
        return delete_permission_or_request(request, permission, False)

    return permission_denied(request)

@login_required
def project_toggle_watch(request, project_slug):
    """Add/Remove watches on a project for a specific user."""
    time.sleep(5)
    if request.method != 'POST':
        return json_error(_('Must use POST to activate'))

    if not settings.ENABLE_NOTICES:
        return json_error(_('Notifation is not enabled'))

    project = get_object_or_404(Project, slug=project_slug)
    url = reverse('project_toggle_watch', args=(project_slug,))

    project_signals = ['project_changed',
                       'project_deleted',
                       'project_component_added',
                       'project_component_changed',
                       'project_component_deleted']
    try:
        result = {
            'style': 'watch_add',
            'title': _('Watch this project'),
            'project': True,
            'url': url,
            'error': None,
        }

        for signal in project_signals:
            notification.stop_observing(project, request.user, signal)

    except notification.ObservedItem.DoesNotExist:
        try:
            result = {
                'style': 'watch_remove',
                'title': _('Stop wathing this project'),
                'project': True,
                'url': url,
                'error': None,
            }

            for signal in project_signals:
                notification.observe(project, request.user, signal, signal)

        except WatchException, e:
            return json_error(e.message, result)
    return json_result(result)


# Components

pr_component_add_change = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.add_component'),
    ('general',  'projects.change_component'),
)
@login_required
@one_perm_required_or_403(pr_component_add_change, 
    (Project, 'slug__exact', 'project_slug'))
def component_create_update(request, project_slug, component_slug=None):
    """
    Create & update components. Handles associated units
    """
    project = get_object_or_404(Project, slug=project_slug)
    if component_slug:
        component = get_object_or_404(Component, slug=component_slug,
                                      project=project)
        unit = component.unit    
    else:
        component = None
        unit = None
    unit_subforms = []
    if request.method == 'POST':
        component_form = ComponentForm(project, request.POST,
                                       instance=component, prefix='component')
        unit_form = UnitForm(request.POST, instance=unit, prefix='unit')
        allow_subform = ComponentAllowSubForm(request.POST, instance=component)
        unit_subforms = unit_sub_forms(unit, request.POST)

        old_i18n_type = None
        old_root = None

        # Submission tab
        if request.POST.has_key('submission_form'):
            if allow_subform.is_valid() and component is not None:
                allow_subform.save()
                # TODO: Add an ActionLog and Notification here for this action
                return HttpResponseRedirect( reverse('component_detail',
                    args=[project_slug, component.slug]),)

        # Checkout tab
        else:
            # TODO: Too much tied, but how can we do it in a better way?
            if request.POST['unit-type']=='tar':
                current_unit_subform = unit_subforms[1]['form']
            else:
                current_unit_subform = unit_subforms[0]['form']

            if component_form.is_valid() and unit_form.is_valid() and \
                current_unit_subform.is_valid():

                if component: 
                    old_i18n_type = component.i18n_type
                component = component_form.save(commit=False)

                if unit:
                    old_root = unit.root
                unit = unit_form.save(commit=False)
                unit.name = component.get_full_name()
                unit.save()
                unit = unit.promote()

                # Here we overwrite the unit fields with the subforms unit fields
                # One thing not very nice is the fact we save the unit two times
                # TODO: Figure out how make it better
                for field in exclusive_fields(type(unit), except_fields=['root']):
                    setattr(unit, field.name, 
                        current_unit_subform.cleaned_data[field.name])
                unit.save()

                component.unit = unit
                component_id = component.id
                component.save()
                component_form.save_m2m()

                # If i18n type changed, clean the POfile objects for this comp.
                if old_i18n_type != component.i18n_type:
                    component.trans.clear_stats()

                # Compare with the old root url and, if it has changed, clear cache
                if old_root and old_root != unit.root:
                    component.clear_cache()

                # ActionLog & Notification
                context = {'component': component}
                object_list = [component.project, component]
                if not component_id:
                    nt = 'project_component_added'
                    action_logging(request.user, object_list, nt, context=context)
                    if settings.ENABLE_NOTICES:
                        txnotification.send_observation_notices_for(component.project,
                                signal=nt, extra_context=context)
                else:
                    nt = 'project_component_changed'
                    action_logging(request.user, object_list, nt, context=context)
                    if settings.ENABLE_NOTICES:
                        txnotification.send_observation_notices_for(component.project,
                                signal=nt, extra_context=context)

                return HttpResponseRedirect(
                    reverse('component_detail',
                        args=[project_slug, component.slug]),)
    else:
        component_form = ComponentForm(project, instance=component,
                                       prefix='component')
        unit_form = UnitForm(instance=unit, prefix='unit')
        allow_subform = ComponentAllowSubForm(instance=component)
        unit_subforms = unit_sub_forms(unit)
    return render_to_response('projects/component_form.html', {
        'component_form': component_form,
        'unit_form': unit_form,
        'unit_subforms': unit_subforms,
        'allow_subform': allow_subform,
        'project' : project,
        'component': component,
        'branch_support': settings.BRANCH_SUPPORT,
    }, context_instance=RequestContext(request))


def component_detail(request, project_slug, component_slug):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    return list_detail.object_detail(
        request,
        queryset = Component.objects.all(),
        object_id=component.id,
        template_object_name = "component",
        )


def component_language_detail(request, project_slug, component_slug,
                                language_code=None):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    try:
        language = Language.objects.get(code=language_code)
    except Language.DoesNotExist:
        language = Language(code=language_code, name=language_code)

    stats = POFile.objects.by_lang_code_and_object(language_code, component)

    # If there no stats, raise a 404
    if not stats:
        raise Http404

    return list_detail.object_detail(
        request,
        queryset = Component.objects.all(),
        object_id=component.id,
        template_object_name = "component",
        template_name = "projects/component_lang_detail.html",
        extra_context = {"language": language,
                         "stats": stats},
        )


pr_component_delete = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.delete_component'),
)
@login_required
@one_perm_required_or_403(pr_component_delete, 
    (Project, 'slug__exact', 'project_slug'))
def component_delete(request, project_slug, component_slug):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    if request.method == 'POST':
        import copy
        component_ = copy.copy(component)
        component.delete()
        request.user.message_set.create(
            message=_("The %s was deleted.") % component.full_name)

        # ActionLog & Notification
        nt = 'project_component_deleted'
        context = {'component': component_}
        action_logging(request.user, [component_.project], nt, context=context)
        if settings.ENABLE_NOTICES:
            txnotification.send_observation_notices_for(component_.project,
                                signal=nt, extra_context=context)

        return HttpResponseRedirect(reverse('project_detail', 
                                     args=(project_slug,)))
    else:
        return render_to_response('projects/component_confirm_delete.html',
                                  {'component': component,},
                                  context_instance=RequestContext(request))

pr_component_set_stats = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.refresh_stats'),
)
@login_required
@one_perm_required_or_403(pr_component_set_stats, 
    (Project, 'slug__exact', 'project_slug'))
def component_set_stats(request, project_slug, component_slug):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    logger.debug("Requested stats calc for component %s" % component.full_name)
    if component.should_calculate:
        # Checkout
        component.prepare()
        # Calculate statistics
        try:
            component.trans.set_stats()
        except FileFilterError:
            logger.debug("File filter does not allow POTFILES.in file name"
                        " for %s component" % component.full_name)
            request.user.message_set.create(message = _(
                "The file filter of this intltool POT-based component does not "
                " seem to allow the POTFILES.in file. Please fix it."))

        except PotDirError:
            logger.debug("There is no 'pot' directory in the set of files. %s does "
                        "not seem to be a Publian like project."
                        % component.full_name)
            request.user.message_set.create(message = _("There is no 'pot' "
                "directory named in the set of files of this Publian like "
                "component. Maybe its file filter is not allowing access to it."))

    else:
        logger.debug("Statistics calculation is disabled for the '%s' component."
                     % component)
        request.user.message_set.create(message = _(
            "This component is not configured for statistics calculation."))

    return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))


pr_component_clear_cache = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.clear_cache'),
)
@login_required
@one_perm_required_or_403(pr_component_clear_cache, 
    (Project, 'slug__exact', 'project_slug'))
def component_clear_cache(request, project_slug, component_slug):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    component.clear_cache()
    return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))


def component_file(request, project_slug, component_slug, filename, 
                   view=False, is_msgmerged=True):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    try:
        content = component.trans.get_file_content(filename, is_msgmerged)
    except (TypeError, IOError):
        raise Http404
    fname = "%s.%s" % (component.full_name, os.path.basename(filename))
    logger.debug("Requested raw file %s" % filename)
    if view:
        try:
            import pygments
            import pygments.lexers
            import pygments.formatters

            lexer = pygments.lexers.GettextLexer()
            formatter = pygments.formatters.HtmlFormatter(linenos='inline')
            encre = re.compile(r'"?Content-Type:.+? charset=([\w_\-:\.]+)')
            m = encre.search(content)
            encoding = 'UTF-8'
            if m:
                try:
                    codecs.lookup(m.group(1))
                    encoding = m.group(1)
                except LookupError:
                    pass
            try:
                # Try to convert to UTF and present it as it should look like
                content = content.decode(encoding)
            except UnicodeDecodeError:
                # Oh well, let's just show it as it is.
                pass
            context = Context({'body': pygments.highlight(content, lexer, formatter),
                               'style': formatter.get_style_defs(),
                               'title': "%s: %s" % (component.full_name,
                                                    os.path.basename(filename))})
            content = loader.get_template('poview.html').render(context)
            mimetype = 'text/html'
        except ImportError:
            # Oh well, no pygments available
            mimetype = 'text/plain'
        response = HttpResponse(content,
            mimetype='%s; charset=UTF-8' % (mimetype,))
        attach = ""
    else:
        response = HttpResponse(content, mimetype='text/plain; charset=UTF-8')
        attach = "attachment;"
    response['Content-Disposition'] = '%s filename=%s' % (attach, fname)
    return response


# for the next two views
pr_component_submit_file = (
    ('granular', 'project_perm.maintain'),
    ('granular', 'project_perm.submit_file'),
    ('general',  'projects.submit_file'),
)
@login_required
@one_perm_required_or_403(pr_component_submit_file, 
    (Project, 'slug__exact', 'project_slug'))
def component_file_edit(request, project_slug, component_slug, filename, 
                        is_msgmerged=True):
    from webtrans.views import transfile_edit
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    #FIXME: This approach hits the database twice!
    # See also: http://transifex.org/ticket/210
    ctype = ContentType.objects.get_for_model(Component)
    pofile = get_object_or_404(POFile, object_id=component.pk,
                               content_type=ctype, filename=filename)

    return transfile_edit(request, pofile.id)


@login_required
@one_perm_required_or_403(pr_component_submit_file, 
    (Project, 'slug__exact', 'project_slug'))
def component_submit_file(request, project_slug, component_slug, 
                          filename=None):

    component = get_object_or_404(Component, slug=component_slug,
                                    project__slug=project_slug)

    # To be used by the ActionLog later
    object_list = [component.project, component]

    if not component.allows_submission:
        request.user.message_set.create(message=_("This component does " 
                            " not allow write access."))
        return HttpResponseRedirect(reverse('projects.views.component_detail', 
                            args=(project_slug, component_slug,)))

    if request.method == 'POST':

        if not request.FILES.has_key('submited_file'):
            request.user.message_set.create(message=_("Please select a " 
                               "file from your system to be uploaded."))
            return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))

        # For a new file
        if not filename:
            if request.POST['targetfile'] == '' and \
               request.POST['newtargetfile'] == '':
                request.user.message_set.create(message=_("Please enter" 
                                       " a target to upload the file."))
                return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))
            elif not request.POST['targetfile'] == '' and \
                 not request.POST['newtargetfile'] == '':
                request.user.message_set.create(message=_("Please enter" 
                                       " only ONE target to upload the file."))
                return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))
            else:
                if request.POST['targetfile'] != '':
                    filename = request.POST['targetfile']
                else:
                    filename = request.POST['newtargetfile']

            if not re.compile(component.file_filter).match(filename):
                request.user.message_set.create(message=_("The target " 
                                       "file does not match with the "
                                       "component file filter"))
                return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))

            if not request.POST['message']:
                request.user.message_set.create(message=
                    _("Enter a commit message"))
                return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))

        # Adding extra field to the instance
        request.FILES['submited_file'].targetfile = filename

        try:
            postats = POFile.objects.get(filename=filename,
                                         object_id=component.id)
            lang_code = postats.language.code
        except (POFile.DoesNotExist, AttributeError):
            postats = None
            lang_code = component.trans.guess_language(filename)

        msg = settings.DVCS_SUBMIT_MSG % {'message': request.POST['message'],
                                          'domain' : request.get_host()}

        try:

            if settings.MSGFMT_CHECK and filename.endswith('.po'):
                logger.debug("Checking %s with msgfmt -c for component %s" % 
                            (filename, component.full_name))
                component.trans.msgfmt_check(request.FILES['submited_file'])

            logger.debug("Checking out for component %s" % component.full_name)
            component.prepare()

            logger.debug("Submitting %s for component %s" % 
                         (filename, component.full_name))

            if component.submission_type=='ssh' or component.unit.type=='tar':
                component.submit(request.FILES, msg, 
                                 get_profile_or_user(request.user))

            if component.submission_type=='email':
                logger.debug("Sending %s for component %s by email" % 
                            (filename, component.full_name))
                submit_by_email(component, request.FILES, request.user)

            logger.debug("Calculating %s stats for component %s" % 
                         (filename, component.full_name))
            if filename.endswith('.po'):
                # TODO: Find out a better way to handle it. We might wand to merge
                # the file with the POT before commmit, but it just must happen when
                # the POT is not broken for intltool based projects.
                component.trans.set_stats_for_lang(lang_code, try_to_merge=False)

                # Getting the new PO file stats after submit it
                postats = POFile.objects.get(filename=filename,
                                                 object_id=component.id)
            else:
                postats = None

            # Append the language to the ActionLog object_list if it exist for
            # this file
            if hasattr(postats, 'language') and postats.language is not None:
                object_list.append(postats.language)

            request.user.message_set.create(message=_("File submitted " 
                               "successfully: %s" % filename))

            # ActionLog & Notification
            nt = 'project_component_file_submitted'
            context = {'component': component, 
                        'filename':filename, 
                        'pofile': postats}
            action_logging(request.user, object_list, nt, context=context)
            if settings.ENABLE_NOTICES:
                txnotification.send_observation_notices_for(component.project,
                       signal=nt, extra_context=context)

        except ValueError: # msgfmt_check
            logger.debug("Msgfmt -c check failed for the %s file." % filename)
            request.user.message_set.create(message=_("Your file does not" \
                                    " pass correctness checks" \
                                    " (msgfmt -c). Please run this command" \
                                    " on your system to see the errors."))
        except StandardError, e:
            logger.debug("Error submiting translation file %s"
                         " for %s component: %r" % (filename,
                         component.full_name, e))
            request.user.message_set.create(message = _(
                "Sorry, your file could not be sent because of an error."))

    else:
        request.user.message_set.create(message = _(
                "Sorry, but you need to send a POST request."))
    return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))


pr_component_lock_file = (
    ('granular', 'project_perm.maintain'),
    ('granular', 'project_perm.submit_file'),
    ('general',  'translations.add_pofilelock'),
    ('general',  'translations.delete_pofilelock'),
)
@login_required
@one_perm_required_or_403(pr_component_lock_file, 
    (Project, 'slug__exact', 'project_slug'))
def component_toggle_lock_file(request, project_slug, component_slug,
                               filename):
    if request.method == 'POST':
        component = get_object_or_404(Component, slug=component_slug,
                                    project__slug=project_slug)
        ctype = ContentType.objects.get_for_model(Component)

        pofile = get_object_or_404(POFile, object_id=component.pk, 
                                   content_type=ctype, filename=filename)

        try:
            lock = POFileLock.objects.get(pofile=pofile)
            if request.user.pk == lock.owner.pk:
                lock.delete()
                request.user.message_set.create(message=_("Lock removed."))
            else:
                request.user.message_set.create(
                    message=_("Error: Only the owner of a lock can remove it."))
        except POFileLock.DoesNotExist:
            lock = POFileLock.objects.create(pofile=pofile, owner=request.user)
            request.user.message_set.create(
                message=_("Lock created. Please don't forget to remove it when "
                "you're done."))
    else:
        request.user.message_set.create(message = _(
                "Sorry, but you need to send a POST request."))
    try:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    except:
        return HttpResponseRedirect(reverse('projects.views.component_detail',
                                        args=(project_slug, component_slug,)))


pr_component_watch_file = (
    ('granular', 'project_perm.maintain'),
    ('general',  'repowatch.add_watch'),
    ('general',  'repowatch.delete_watch'),
)
@login_required
@one_perm_required_or_403(pr_component_watch_file, 
    (Project, 'slug__exact', 'project_slug'))
def component_toggle_watch(request, project_slug, component_slug, filename):
    """Add/Remove a watch for a path on a component for a specific user."""

    if request.method != 'POST':
        return json_error(_('Must use POST to activate'))

    if not settings.ENABLE_NOTICES:
        return json_error(_('Notifation is not enabled'))

    component = get_object_or_404(Component, slug=component_slug,
                                project__slug=project_slug)
    ctype = ContentType.objects.get_for_model(Component)

    pofile = get_object_or_404(POFile, object_id=component.pk, 
                               content_type=ctype, filename=filename)

    url = reverse('component_toggle_watch', args=(project_slug, component_slug, 
                                                  filename))
    try:
        watch = Watch.objects.get(path=filename, component=component, 
                                  user__id__exact=request.user.id)
        watch.user.remove(request.user)
        result = {
            'style': 'watch_add',
            'title': watch_titles['watch_add_title'],
            'id': pofile.id,
            'url': url,
            'error': None,
        }
        notification.stop_observing(pofile, request.user, 
                            signal='project_component_file_changed')
    except Watch.DoesNotExist:
        try:
            Watch.objects.add_watch(request.user, component, filename)
            result = {
                'style': 'watch_remove',
                'title': watch_titles['watch_remove_title'],
                'id': pofile.id,
                'url': url,
                'error': None,
            }
            notification.observe(pofile, request.user,
                                 'project_component_file_changed',
                                 signal='project_component_file_changed')
        except WatchException, e:
            return json_error(e.message, result)
    return json_result(result)

