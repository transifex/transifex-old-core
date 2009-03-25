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
from django.views.generic import create_update, list_detail
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import feed

import settings

from projects.models import Project, Component
from projects.forms import ProjectForm, ComponentForm, UnitForm
from txcommon.log import logger
from actionlog.models import (log_addition, log_change, log_deletion, 
                              log_submission)
from translations.lib.types.pot import FileFilterError
from translations.models import (POFile, POFileLock)
from translations.models import POFile
from languages.models import Language
from txcommon.decorators import perm_required_with_403

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
            if not project_id:
                log_addition(request, project)
            else:
                log_change(request, project, 'This project has been changed.')
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
        log_deletion(request, project_, project_.name)
        request.user.message_set.create(
            message=_("The %s was deleted.") % project.name)
        return HttpResponseRedirect(reverse('project_list'))
    else:
        return render_to_response(
            'projects/project_confirm_delete.html', {'project': project,},
            context_instance=RequestContext(request))


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
            unit = unit_form.save(commit=False)            
            unit.name = component.get_full_name()
            unit.save()
            component.unit = unit
            component_id = component.id
            component.save()
            component_form.save_m2m()
            if not component_id:
                log_addition(request, component)
            else:
                log_change(request, component,
                           'This component has been changed.')
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
        log_deletion(request, component_, component_.name)        
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
    component.prepare_repo()
    # Calculate statistics
    try:
        component.trans.set_stats()
    except FileFilterError:
        logger.debug("File filter does not allow POTFILES.in file name"
                     " for %s component" % component.full_name)
        # TODO: Figure out why gettext is not working here
        request.user.message_set.create(message = (
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
    if not component.allows_submission:
        request.user.message_set.create(message=("This component does " 
                            " not allow white access."))
        return HttpResponseRedirect(reverse('projects.views.component_detail', 
                            args=(project_slug, component_slug,)))

    if request.method == 'POST':

        if not request.FILES.has_key('submited_file'):
            # TODO: Figure out why gettext is not working here
            request.user.message_set.create(message=("Please select a " 
                               "file from your system to be uploaded."))
            return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))

        # For a new file
        if not filename:
            if request.POST['targetfile'] == '' and \
               request.POST['newtargetfile'] == '':
                # TODO: Figure out why gettext is not working here
                request.user.message_set.create(message=("Please enter" 
                                       " a target to upload the file."))
                return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))
            elif not request.POST['targetfile'] == '' and \
                 not request.POST['newtargetfile'] == '':
                # TODO: Figure out why gettext is not working here
                request.user.message_set.create(message=("Please enter with" 
                                       " only ONE target to upload the file."))
                return HttpResponseRedirect(reverse('projects.views.component_detail', 
                                args=(project_slug, component_slug,)))
            else:
                if request.POST['targetfile'] != '':
                    filename = request.POST['targetfile']
                else:
                    filename = request.POST['newtargetfile']

            if not re.compile(component.file_filter).match(filename):
                # TODO: Figure out why gettext is not working here
                request.user.message_set.create(message=("The target " 
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
            lang_name = filename
            lang_code = component.trans.guess_language(filename)

        # TODO: put it somewhere else using the settings.py
        msg="Sending translation for %s" % lang_name

        try:

            if settings.MSGFMT_CHECK:
                logger.debug("Checking %s with msgfmt -c for component %s" % 
                            (filename, component.full_name))
                for contents in request.FILES['submited_file'].chunks():
                    component.trans.msgfmt_check(contents)

            logger.debug("Checking out for component %s" % component.full_name)
            component.prepare_repo()

            logger.debug("Submitting %s for component %s" % 
                         (filename, component.full_name))
            component.submit(request.FILES, msg, request.user)

            logger.debug("Calculating %s stats for component %s" % 
                         (filename, component.full_name))
            component.trans.set_stats_for_lang(lang_code)

            request.user.message_set.create(message=("File submitted " 
                               "successfully: %s" % filename))
            log_submission(request, component,
                           'A translation has been submitted for %s' % lang_name)
        except ValueError: # msgfmt_check
            logger.debug("Msgfmt -c check failed for the %s file." % filename)
            request.user.message_set.create(message=("Your file does not" \
                                    " pass by the check for correctness" \
                                    " (msgfmt -c). Please run this command" \
                                    " on your system to see the errors."))
        except StandardError, e:
            logger.debug("Error submiting translation file %s"
                         " for %s component: %r" % (filename,
                         component.full_name, e))
           # TODO: Figure out why gettext is not working here
            request.user.message_set.create(message = (
                "Sorry, an error is causing troubles to send your file."))

    else:
        # TODO: Figure out why gettext is not working here
        request.user.message_set.create(message = (
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
                # TODO: Figure out why gettext is not working here
                request.user.message_set.create(message="Lock removed.")
            else:
                # TODO: Figure out why gettext is not working here
                request.user.message_set.create(
                    message="Error: Only the owner of a lock can remove it.")
        except POFileLock.DoesNotExist:
            lock = POFileLock.objects.create(pofile=pofile, owner=request.user)
            # TODO: Figure out why gettext is not working here
            request.user.message_set.create(
                message="Lock created. Please don't forget to remove it when "
                "you're done.")
    else:
        # TODO: Figure out why gettext is not working here
        request.user.message_set.create(message = (
                "Sorry, but you need to send a POST request."))
    try:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    except:
        return HttpResponseRedirect(reverse('projects.views.component_detail',
                                        args=(project_slug, component_slug,)))
