from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib.syndication.feeds import Feed
from django.contrib.sites.models import Site
from txcollections.models import Collection, CollectionRelease as Release
from translations.models import POFile
from models import Language
from txcommon.templatetags.txcommontags import key_sort
current_site = Site.objects.get_current()

class AllLanguages(Feed):
    current_site = Site.objects.get_current()
    title = _("Languages on %(site_name)s") % {
        'site_name': current_site.name }
    link = current_site.domain
    description = _("The languages spoken on %s.") % current_site.name

    def items(self):
        return Language.objects.all()

class LanguageReleaseFeed(Feed):

    def get_object(self, bits):
        if len(bits) != 3:
            raise ObjectDoesNotExist
        language_slug, collection_slug, release_slug = bits
        self.collection = get_object_or_404(Collection, 
                                            slug__exact=collection_slug)
        self.release = get_object_or_404(Release, slug__exact=release_slug,
                                         collection=self.collection)
        return Language.objects.get(code__exact=bits[0])

    def title(self, obj):
        return _("%(site_name)s: %(language)s :: %(release)s release") % {
            'site_name': current_site.name,
            'language': obj.name,
            'release': self.release.full_name,}

    def description(self, obj):
        return _("Latest translations for %(language)s language in "
                 "%(release)s release.") % {
                   'site_name': current_site.name,
                   'language': obj.name,
                   'release': self.release.full_name,}
                 
    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def items(self, obj):
        stats = POFile.objects.by_language_and_release(obj, self.release)[:100]
        return key_sort(stats, 'object.name', 'object.project.name', '-trans_perc')

    def item_link(self, item):
        return item.object.get_absolute_url()
