# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth.decorators import login_required

from actionlog.models import action_logging
from languages.models import Language
from projects.models import Project, Component, Release
from projects.forms import ReleaseForm
from projects.permissions import (pr_release_add_change, pr_release_delete)
from translations.models import POFile

# Temporary
from txcommon import notifications as txnotification
from txcommon.decorators import one_perm_required_or_403
from txcommon.log import logger


##############################################
# Releases

@login_required
@one_perm_required_or_403(pr_release_add_change,
    (Project, 'slug__exact', 'project_slug'))
def release_create_update(request, project_slug, release_slug=None, *args, **kwargs):
    project = get_object_or_404(Project, slug__exact=project_slug)
    if release_slug:
        release = get_object_or_404(Release, slug=release_slug,
                                    project__slug=project_slug)
    else:
        release = None
    if request.method == 'POST':
        release_form = ReleaseForm(project, request.POST, instance=release)
        if release_form.is_valid():
            release = release_form.save()

            return HttpResponseRedirect(
                reverse('release_detail',
                         args=[project_slug, release.slug]))
    else:
        release_form = ReleaseForm(project, instance=release)

    return render_to_response('projects/release_form.html', {
        'form': release_form,
        'project': project,
        'release': release,
    }, context_instance=RequestContext(request))


def release_detail(request, project_slug, release_slug):
    release = get_object_or_404(Release, slug=release_slug,
                                project__slug=project_slug)
    pofile_list = POFile.objects.by_release_total(release)
    return render_to_response('projects/release_detail.html', {
        'release': release,
        'project': release.project,
        'pofile_list': pofile_list,
    }, context_instance=RequestContext(request))


def release_language_detail(request, project_slug, release_slug, language_code):

    language = get_object_or_404(Language, code__iexact=language_code)
    project = get_object_or_404(Project, slug__exact=project_slug)
    release = get_object_or_404(Release, slug__exact=release_slug,
        project__id=project.pk)
    pofile_list = POFile.objects.by_language_and_release_total(language, release)
    untrans_comps = Component.objects.untranslated_by_lang_release(language, 
        release)
    return render_to_response('projects/release_language_detail.html', {
        'pofile_list': pofile_list,
        'project': project,
        'release': release,
        'language': language,
        'untrans_comps': untrans_comps,
    }, context_instance=RequestContext(request))


@login_required
@one_perm_required_or_403(pr_release_delete, 
    (Project, 'slug__exact', 'project_slug'))
def release_delete(request, project_slug, release_slug):
    release = get_object_or_404(Release, slug=release_slug,
                                project__slug=project_slug)
    if request.method == 'POST':
        import copy
        release_ = copy.copy(release)
        release.delete()
        request.user.message_set.create(
            message=_("%s was deleted.") % release.full_name)

        # ActionLog & Notification
        nt = 'project_release_deleted'
        context = {'release': release_}
        action_logging(request.user, [release_.project], nt, context=context)
        if settings.ENABLE_NOTICES:
            txnotification.send_observation_notices_for(release_.project,
                                signal=nt, extra_context=context)

        return HttpResponseRedirect(reverse('project_detail', 
                                     args=(project_slug,)))
    else:
        return render_to_response('projects/release_confirm_delete.html',
                                  {'release': release,},
                                  context_instance=RequestContext(request))


def release_language_download(request, project_slug, release_slug, 
        language_code, filetype):
    """
    Download a compressed file of all files for a release-language.
    """
    language = get_object_or_404(Language, code__iexact=language_code)
    project = get_object_or_404(Project, slug__exact=project_slug)
    release = get_object_or_404(Release, slug__exact=release_slug,
        project__id=project.pk)
    pofile_list = POFile.objects.by_language_and_release_total(language, release)

    filename = '%s.%s_%s' % (project.slug, release.slug, language.code)
    from translations.util.compressed import POCompressedArchive
    try:
        archive = POCompressedArchive(pofile_list, filename, filetype)
        response = HttpResponse(file(archive.file_path).read())
        response['Content-Disposition'] = 'attachment; filename=%s' % archive.filename
        response['Content-Type'] = archive.content_type
        archive.cleanup()
    except NotImplementedError:
        raise Http404
    return response


