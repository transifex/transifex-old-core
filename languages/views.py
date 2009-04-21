import os

from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import list_detail
from django.utils.translation import ugettext_lazy as _
from django.contrib.syndication.views import feed
from django.template import RequestContext

from translations.models import POFile
from models import Language
from txcollections.models import (Collection, CollectionRelease as Release)
from projects.models import Component

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


def language_release_feed(request,
                          language_slug, collection_slug, release_slug,
                          slug=None, param='', feed_dict=None,):
    param = '%s/%s/%s' % (language_slug, collection_slug, release_slug)
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)


def language_detail(request, slug, *args, **kwargs):
    language = get_object_or_404(Language, code__iexact=slug)
    pofile_list = POFile.objects.by_language(language)
    return list_detail.object_detail(
        request,
        object_id=language.id,
        extra_context = {'pofile_list': pofile_list,
                         'collection_list': Collection.objects.all()},
        *args, **kwargs
    )

def get_lang_rel_objs(language_slug, collection_slug, release_slug):
    """
    Shortcut function to return appropriate objects for lang-rel views.
    """
    language = get_object_or_404(Language, code__iexact=language_slug)
    collection = get_object_or_404(Collection, 
                                   slug__exact=collection_slug)
    release = get_object_or_404(Release, slug__exact=release_slug,
                                collection=collection)
    pofile_list = POFile.objects.by_language_and_release_total(language, release)
    return language, collection, release, pofile_list

def language_release(request, slug, collection_slug, release_slug):
    language, collection, release, pofile_list = get_lang_rel_objs(
        slug, collection_slug, release_slug)
    untrans_comps = Component.objects.untranslated_by_lang_release(language, 
                                                                   release)

    return render_to_response('languages/language_release.html', {
        'pofile_list': pofile_list,
        'release': release,
        'language': language,
        'untrans_comps': untrans_comps,
    }, context_instance=RequestContext(request))


def language_release_download(request, slug, collection_slug, release_slug,
                              filetype):
    """
    Download a compressed file of all files for a language-release.
    """
    language, collection, release, pofile_list = get_lang_rel_objs(
        slug, collection_slug, release_slug)

    filename = '%s.%s_%s' % (language.code, collection.slug, release.slug)
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
