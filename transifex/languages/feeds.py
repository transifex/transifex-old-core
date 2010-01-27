from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib.syndication.feeds import Feed
from django.contrib.sites.models import Site
from translations.models import POFile
from models import Language
from txcommon.utils import key_sort
current_site = Site.objects.get_current()

class AllLanguages(Feed):
    current_site = Site.objects.get_current()
    title = _("Languages on %(site_name)s") % {
        'site_name': current_site.name }
    link = current_site.domain
    description = _("The languages spoken on %s.") % current_site.name

    def items(self):
        return Language.objects.all()
