# -*- coding: utf-8 -*-
import os
import re
import codecs
import pygments
import pygments.lexers
import pygments.formatters

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
from django.contrib.syndication.views import feed

from projects.models import Project, Component
from projects.forms import ProjectForm, ComponentForm, UnitForm
from projects import signals
from txcommon.log import logger
from actionlog.models import action_logging
from translations.lib.types.pot import FileFilterError
from translations.models import (POFile, POFileLock)
from languages.models import Language
from txcommon.decorators import perm_required_with_403
from txcommon.views import (json_result, json_error)
from repowatch import WatchException, watch_titles
from repowatch.models import Watch
from notification import models as notification

# Temporary
from txcommon import notifications as txnotification

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

@login_required
@perm_required_with_403('projects.add_project')
@perm_required_with_403('projects.change_project')
def project_create_update(request, project_slug=None):

    if project_slug:
        project = get_object_or_404(Project, slug=project_slug)
    else:
        project = None

    if request.method == 'POST':
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
        project_form = ProjectForm(instance=project, prefix='project')

    return render_to_response('projects/project_form.html', {
        'project_form': project_form,
        'project': project,
    }, context_instance=RequestContext(request))


@login_required
@perm_required_with_403('projects.delete_project')
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
        action_logging(request.user, project_, nt, context=context)

        return HttpResponseRedirect(reverse('project_list'))
    else:
        return render_to_response(
            'projects/project_confirm_delete.html', {'project': project,},
            context_instance=RequestContext(request))


@login_required
def project_toggle_watch(request, project_slug):
    """ Add/Remove watches on a project for a specific user """

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

@login_required
@perm_required_with_403('projects.add_component')
@perm_required_with_403('projects.change_component')
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
    if request.method == 'POST':
        component_form = ComponentForm(project, request.POST,
                                       instance=component, prefix='component')
        unit_form = UnitForm(request.POST, instance=unit, prefix='unit')
        if component_form.is_valid() and unit_form.is_valid():
            component = component_form.save(commit=False)
            if unit:
                old_root = unit.root
            else:
                old_root = None
            unit = unit_form.save(commit=False)            
            unit.name = component.get_full_name()
            unit.save()
            component.unit = unit
            component_id = component.id
            component.save()
            component_form.save_m2m()

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
    return render_to_response('projects/component_form.html', {
        'component_form': component_form,
        'unit_form': unit_form,
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


@login_required
@perm_required_with_403('projects.delete_component')
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
@perm_required_with_403('projects.refresh_stats')
def component_set_stats(request, project_slug, component_slug):
    component = get_object_or_404(Component, slug=component_slug,
                                  project__slug=project_slug)
    logger.debug("Requested stats calc for component %s" % component.full_name)
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
    return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))


@login_required
@perm_required_with_403('projects.clear_cache')
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
    except IOError:
        raise Http404
    fname = "%s.%s" % (component.full_name, os.path.basename(filename))
    logger.debug("Requested raw file %s" % filename)
    if view:
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
        context = Context({'body': pygments.highlight(content.decode(
                                        encoding), lexer, formatter),
                           'style': formatter.get_style_defs(),
                           'title': "%s: %s" % (component.full_name,
                                                os.path.basename(filename))})
        content = loader.get_template('poview.html').render(context)
        response = HttpResponse(content, mimetype='text/html; charset=UTF-8')
        attach = ""
    else:
        response = HttpResponse(content, mimetype='text/plain; charset=UTF-8')
        attach = "attachment;"
    response['Content-Disposition'] = '%s filename=%s' % (attach, fname)
    return response

@login_required
@perm_required_with_403('projects.submit_file')
def component_submit_file(request, project_slug, component_slug, 
                          filename=None):

    component = get_object_or_404(Component, slug=component_slug,
                                    project__slug=project_slug)

    # To be used by the ActionLog later
    object_list = [component.project, component]

    if not component.allows_submission:
        request.user.message_set.create(message=_("This component does " 
                            " not allow white access."))
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
                request.user.message_set.create(message=_("Please enter with" 
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
        # Adding extra field to the instance
        request.FILES['submited_file'].targetfile = filename

        try:
            postats = POFile.objects.get(filename=filename,
                                         object_id=component.id)
            lang_name = postats.language.name
            lang_code = postats.language.code
        except (POFile.DoesNotExist, AttributeError):
            postats = None
            lang_name = filename
            lang_code = component.trans.guess_language(filename)

        # TODO: put it somewhere else using the settings.py
        msg=_("Sending translation for %s") % lang_name

        try:

            if settings.MSGFMT_CHECK and filename.endswith('.po'):
                logger.debug("Checking %s with msgfmt -c for component %s" % 
                            (filename, component.full_name))
                component.trans.msgfmt_check(request.FILES['submited_file'])

            logger.debug("Checking out for component %s" % component.full_name)
            component.prepare()

            logger.debug("Submitting %s for component %s" % 
                         (filename, component.full_name))
            component.submit(request.FILES, msg, request.user)

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
                                    " pass by the check for correctness" \
                                    " (msgfmt -c). Please run this command" \
                                    " on your system to see the errors."))
        except StandardError, e:
            logger.debug("Error submiting translation file %s"
                         " for %s component: %r" % (filename,
                         component.full_name, e))
            request.user.message_set.create(message = _(
                "Sorry, an error is causing troubles to send your file."))

    else:
        request.user.message_set.create(message = _(
                "Sorry, but you need to send a POST request."))
    return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))


@login_required
@perm_required_with_403('translations.add_pofilelock')
@perm_required_with_403('translations.delete_pofilelock')
def component_toggle_lock_file(request, project_slug, component_slug,
                               filename):
    if request.method == 'POST':
        component = get_object_or_404(Component, slug=component_slug,
                                    project__slug=project_slug)
        pofile = get_object_or_404(POFile, component=component, filename=filename)

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


@login_required
@perm_required_with_403('repowatch.add_watch')
@perm_required_with_403('repowatch.delete_watch')
def component_toggle_watch(request, project_slug, component_slug, filename):
    """ Add/Remove a watch for a path on a component for a specific user """

    if request.method != 'POST':
        return json_error(_('Must use POST to activate'))

    component = get_object_or_404(Component, slug=component_slug,
                                project__slug=project_slug)
    pofile = get_object_or_404(POFile, component=component, filename=filename)

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

