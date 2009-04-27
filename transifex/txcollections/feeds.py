from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib.syndication.feeds import (Feed, FeedDoesNotExist)
from django.contrib.sites.models import Site

from translations.models import POFile
from txcollections.models import (Collection, CollectionRelease as Release)
from txcommon.templatetags.txcommontags import key_sort

current_site = Site.objects.get_current()

class LatestCollections(Feed):
    title = _("Latest collections on %(site_name)s") % {
        'site_name': current_site.name }
    link = current_site.domain
    description = _("Updates on changes and additions to collections.")

    def items(self):
        return Collection.objects.order_by('-created')[:10]


class CollectionFeed(Feed):

    def get_object(self, bits):
        # In case of "/rss/name/foo/bar/baz/", or other such clutter,
        # check that the bits parameter has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Collection.objects.get(slug__exact=bits[0])

    def title(self, obj):
        return _("%(site_name)s: %(collection)s collection") % {
            'site_name': current_site.name,
            'collection': obj.name }

    def description(self, obj):
        return _("Latest releases in the %s collection.") % obj.name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def items(self, obj):
        return obj.releases.order_by('-name')[:50]


class ReleaseLanguagesFeed(Feed):
    """
    A feed for all the languages for this release.
    """
    
    def get_object(self, bits):
        if len(bits) != 2:
            raise ObjectDoesNotExist
        collection_slug, release_slug = bits
        self.collection = get_object_or_404(Collection, 
                                            slug__exact=collection_slug)
        self.release = get_object_or_404(Release, slug__exact=release_slug,
                                         collection=self.collection)
        return self.release

    def title(self, obj):
        return _("%(site_name)s: %(collection)s :: %(release)s release") % {
            'site_name': current_site.name,
            'collection': self.collection.name,
            'release': obj.name,}

    def description(self, obj):
        return _("Translation statistics for all languages against "
                 "%s release.") % obj.name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def items(self, obj):
        pofiles = [p for p in POFile.objects.by_release_total(obj)]
        pofiles_sorted = key_sort(pofiles, 'language.name', '-trans_perc')
        return pofiles_sorted[:200]

    def item_link(self, obj):
        return obj.object.get_absolute_url()