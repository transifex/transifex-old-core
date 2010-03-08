# -*- coding: utf-8 -*-
import os
import re

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader, Context
from django.views.generic import list_detail
from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

from actionlog.models import action_logging
from authority.views import permission_denied
from codebases.forms import UnitForm
from languages.models import Language
from notification import models as notification
from projects.models import Project, Component
from projects.forms import ComponentForm, ComponentAllowSubForm
from projects.permissions import *
from projects.permissions.project import ProjectPermission
from projects.signals import submission_error
from repowatch import WatchException, watch_titles
from repowatch.models import Watch
from submissions.utils import (submit_by_email, msgfmt_error_send_mail)
from reviews.views import review_add
from teams.models import Team
from translations.lib.types.pot import FileFilterError, MsgfmtCheckError
from translations.lib.types.publican import PotDirError
from translations.models import POFile, POFileLock

# Temporary
from txcommon import notifications as txnotification

from txcommon.decorators import one_perm_required_or_403
from txcommon.forms import unit_sub_forms
from txcommon.log import logger
from txcommon.models import exclusive_fields, get_profile_or_user
from txcommon.views import json_result, json_error

# Cache the current site
current_site = Site.objects.get_current()

# Components
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
        unit_subforms = unit_sub_forms(unit, request.POST,
            project.blacklist_vcsunits)
        old_i18n_type = None
        old_root = None

        # Checkout tab
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
                component.trans.clean_stats()

            # Compare with the old root url and, if it has changed, clear cache
            if old_root and old_root != unit.root:
                component.allows_submission = False
                component.save()
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
        unit_subforms = unit_sub_forms(unit, None,
            project.blacklist_vcsunits)

    return render_to_response('projects/component_form.html', {
        'component_form': component_form,
        'unit_form': unit_form,
        'unit_subforms': unit_subforms,
        'project' : project,
        'component': component,
        'branch_support': settings.BRANCH_SUPPORT,
    }, context_instance=RequestContext(request))


@login_required
@one_perm_required_or_403(pr_component_add_change, 
    (Project, 'slug__exact', 'project_slug'))
def component_submission_edit(request, project_slug, component_slug):
    """
    Create & update components. Handles associated units
    """
    project = get_object_or_404(Project, slug=project_slug)
    component = get_object_or_404(Component, slug=component_slug,
        project=project)
    submission_types = \
        settings.SUBMISSION_CHOICES[component.unit.type].items()
    if request.method == 'POST':
        allow_submission_form = ComponentAllowSubForm(
            submission_types=submission_types, 
            data=request.POST, 
            instance=component)

        if allow_submission_form.is_valid():
            allow_submission_form.save()
            # TODO: Add an ActionLog and Notification here for this action
            return HttpResponseRedirect( reverse('component_detail',
                args=[project_slug, component.slug]),)

    else:
        allow_submission_form = ComponentAllowSubForm(
            submission_types=submission_types,
            instance=component)

    return render_to_response('projects/component_form.html', {
        'allow_submission_form': allow_submission_form,
        'project' : project,
        'component': component,
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
                        "not seem to be a Publican like project."
                        % component.full_name)
            request.user.message_set.create(message = _("There is no 'pot' "
                "directory named in the set of files of this Publican like "
                "component. Maybe its file filter is not allowing access to it."))

    else:
        logger.debug("Statistics calculation is disabled for the '%s' component."
                     % component)
        request.user.message_set.create(message = _(
            "This component is not configured for statistics calculation."))

    return HttpResponseRedirect(reverse('projects.views.component.component_detail', 
                                args=(project_slug, component_slug,)))



@login_required
@one_perm_required_or_403(pr_component_clear_cache, 
    (Project, 'slug__exact', 'project_slug'))
def component_clear_cache(request, project_slug, component_slug):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    component.clear_cache()
    return HttpResponseRedirect(reverse('projects.views.component.component_detail', 
                                args=(project_slug, component_slug,)))


def component_file(request, project_slug, component_slug, filename, 
                   view=False, is_msgmerged=True):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    try:
        content = component.trans.get_file_contents(filename, is_msgmerged)
    except (TypeError, IOError):
        raise Http404
    base_filename = os.path.basename(filename)
    full_filename = "%s.%s" % (component.full_name, base_filename)
    logger.debug("Requested raw file %s" % full_filename)
    if view:
        try:
            import codecs
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
            content = content.decode(encoding)
            context = Context({'body': pygments.highlight(content, lexer, formatter),
                               'style': formatter.get_style_defs(),
                               'title': "%s: %s" % (component.full_name,
                                                    base_filename)})
            content = loader.get_template('poview.html').render(context)
            mimetype = 'text/html'
        except (UnicodeDecodeError, ImportError), e:
            # Oh well, pygments is unavailable for one reason or another.
            # Display as plaintext
            submission_error.send(sender=component, filename=base_filename,
                                  message=e)
            mimetype = 'text/plain'
        response = HttpResponse(content,
            mimetype='%s; charset=UTF-8' % (mimetype,))
        attach = ""
    else:
        response = HttpResponse(content, mimetype='text/plain; charset=UTF-8')
        attach = "attachment;"
    response['Content-Disposition'] = '%s filename=%s' % (attach, full_filename)
    return response


@login_required
#@one_perm_required_or_403(pr_component_submit_file, 
#    (Project, 'slug__exact', 'project_slug'))
def component_submit_file(request, project_slug, component_slug, 
                          filename=None, submitted_file=None):

    component = get_object_or_404(Component, slug=component_slug,
                                    project__slug=project_slug)

    # To be used by the ActionLog later
    object_list = [component.project, component]

    if not component.allows_submission:
        request.user.message_set.create(message=_("This component does " 
                            " not allow write access."))
        return HttpResponseRedirect(reverse('projects.views.component.component_detail', 
                            args=(project_slug, component_slug,)))

    if request.method == 'POST':

        if not request.FILES.has_key('submitted_file') and not submitted_file:
            request.user.message_set.create(message=_("Please select a " 
                               "file from your system to be uploaded."))
            return HttpResponseRedirect(reverse('projects.views.component.component_detail', 
                                args=(project_slug, component_slug,)))

        # For a new file
        if not filename:
            if not request.POST['targetfile'] and not request.POST['newtargetfile']:
                request.user.message_set.create(message=_("Please enter" 
                                       " a target to upload the file."))
                return HttpResponseRedirect(reverse('projects.views.component.component_detail', 
                                args=(project_slug, component_slug,)))
            elif request.POST['targetfile'] and request.POST['newtargetfile']:
                request.user.message_set.create(message=_("Please enter" 
                                       " only ONE target to upload the file."))
                return HttpResponseRedirect(reverse('projects.views.component.component_detail', 
                                args=(project_slug, component_slug,)))
            else:
                if request.POST['targetfile']:
                    filename = request.POST['targetfile']
                else:
                    filename = request.POST['newtargetfile']

            if not re.compile(component.file_filter).match(filename):
                request.user.message_set.create(message=_("The target " 
                                       "file does not match the "
                                       "component file filter"))
                return HttpResponseRedirect(reverse('projects.views.component.component_detail', 
                                args=(project_slug, component_slug,)))

            if not request.POST.get('message', None):
                request.user.message_set.create(message=
                    _("Enter a commit message"))
                return HttpResponseRedirect(reverse('projects.views.component.component_detail', 
                                args=(project_slug, component_slug,)))

        if not submitted_file:
            # Adding extra attr to the instance
            request.FILES['submitted_file'].targetfile = filename
            
            file_dict = {'submitted_file':request.FILES['submitted_file']}
            submitted_file = request.FILES['submitted_file']
        else:
            submitted_file.targetfile = filename
            file_dict = {'submitted_file':submitted_file}
            
        try:
            postats = POFile.objects.get(filename=filename,
                                         object_id=component.id)
            language = postats.language
            lang_code = postats.language.code
            team_name = language.name
        except (POFile.DoesNotExist, AttributeError):
            language, postats = None, None
            team_name = lang_code = component.trans.guess_language(filename)

        team = Team.objects.get_or_none(component.project, lang_code)
        if team:
            object_list.append(team)

        check = ProjectPermission(request.user)

        review_check_denied = False
        # Send the file for review instead of immediately submit it
        if request.POST.get("submit_for_review", None):
            if check.submit_file(team or component.project) or \
                request.user.has_perm('reviews.add_poreviewrequest'):
                return review_add(request, component, submitted_file, language)
            else:
                review_check_denied = True

        if review_check_denied or not check.submit_file(team or component.project):
            request.user.message_set.create(message=
                _("You need to be in the '%s' team of this project for "
                  "being able to send translations to that file "
                  "target.") % team_name)
            return HttpResponseRedirect(reverse('component_detail', 
                            args=(project_slug, component_slug,)))

        try:
            if settings.MSGFMT_CHECK and filename.endswith('.po'):
                logger.debug("Checking %s with msgfmt -c for component %s" % 
                            (filename, component.full_name))
                component.trans.msgfmt_check(submitted_file)
            logger.debug("Checking out for component %s" % component.full_name)
            component.prepare()

            logger.debug("Submitting %s for component %s" % 
                         (filename, component.full_name))

            if component.submission_type=='ssh' or component.unit.type=='tar':

                # Rendering the commit message
                new_stats = component.trans.get_po_stats(submitted_file)
                completion = component.trans.get_stats_completion(new_stats)
                status = component.trans.get_stats_status(new_stats)
                message = request.POST.get('message', None)
                if not message:
                    message = "Updated %s translation to %s%%" % (
                        (language or lang_code), completion)

                msg = settings.DVCS_SUBMIT_MSG % {'message': message,
                                                  'status': status,
                                                  'domain' : current_site.domain }

                component.submit(file_dict, msg, 
                                 get_profile_or_user(request.user))

            elif component.submission_type=='email':
                logger.debug("Sending %s for component %s by email" % 
                            (filename, component.full_name))
                submit_by_email(component, file_dict, request.user)

            if filename.endswith('.po') and component.submission_type!='email' or \
                component.unit.type=='tar':
                logger.debug("Calculating %s stats for component %s" % 
                            (filename, component.full_name))
                # TODO: Find out a better way to handle it. We might wand to merge
                # the file with the POT before commmit, but it just must happen when
                # the POT is not broken for intltool based projects.
                component.trans.set_file_stats(filename, is_msgmerged=False)

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

        except MsgfmtCheckError:
            logger.debug("Msgfmt -c check failed for file %s." % filename)
            if (hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST and
                request.user.email):
                msgfmt_error_send_mail(component, request.user, submitted_file,
                                       file_dict, filename)
                request.user.message_set.create(message=_(
                    "Your file does not pass the correctness checks "
                    "(msgfmt -c). Your file has been e-mailed to you to avoid "
                    "losing any work."))
            else:
                request.user.message_set.create(message=_(
                    "Your file does not pass the correctness checks "
                    "(msgfmt -c). Please run this command on your system to "
                    "see the errors. We couldn't send you an email to preserve "
                    "your work because you haven't registered an email address. "
                    "Please do so now to avoid such issues in the future."))

        except StandardError, e:
            logger.debug("Error submiting translation file %s"
                         " for %s component: %s" % (filename,
                         component.full_name, str(e)))
            request.user.message_set.create(message = _(
                "Sorry, your file could not be sent because of an error."))
    else:
        request.user.message_set.create(message = _(
                "Sorry, but you need to send a POST request."))
    return HttpResponseRedirect(reverse('projects.views.component.component_detail', 
                                args=(project_slug, component_slug,)))


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
        return HttpResponseRedirect(reverse('projects.views.component.component_detail',
                                        args=(project_slug, component_slug,)))


@login_required
def component_toggle_watch(request, project_slug, component_slug, filename):
    """Add/Remove a watch for a path on a component for a specific user."""

    if request.method != 'POST':
        return json_error(_('Must use POST to activate'))

    if not settings.ENABLE_NOTICES:
        return json_error(_('Notification is not enabled'))

    component = get_object_or_404(Component, slug=component_slug,
                                project__slug=project_slug)
    ctype = ContentType.objects.get_for_model(Component)

    pofile = get_object_or_404(POFile, object_id=component.pk, 
                               content_type=ctype, filename=filename)

    # FIXME: It's kinda redundancy, only a decorator should be enough
    # Also it's only accepting granular permissions
    check = ProjectPermission(request.user)
    if not check.submit_file(pofile) and not \
        request.user.has_perm('repowatch.add_watch') and not \
        request.user.has_perm('repowatch.delete_watch'):
        return permission_denied(request)

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

