from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.syndication.feeds import FeedDoesNotExist
from django.contrib.syndication.views import Feed
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.timesince import timesince
from django.template.defaultfilters import linebreaks, escape, striptags

from transifex.actionlog.models import LogEntry
import re

from notification.models import Notice
from txcommon.notification_atomformat import Feed as notification_Feed


current_site = Site.objects.get_current()

ITEMS_PER_FEED = getattr(settings, 'ITEMS_PER_FEED', 20)
DEFAULT_HTTP_PROTOCOL = getattr(settings, "DEFAULT_HTTP_PROTOCOL", "http")


class BaseNoticeFeed(notification_Feed):
    def item_id(self, notification):
        return "%s://%s%s" % (
            DEFAULT_HTTP_PROTOCOL,
            Site.objects.get_current().domain,
            notification.get_absolute_url(),
        )
    
    def item_title(self, notification):
        return striptags(notification.message)
    
    def item_updated(self, notification):
        return notification.added
    
    def item_published(self, notification):
        return notification.added
    
    def item_content(self, notification):
        return {"type" : "html", }, linebreaks(escape(notification.message))
    
    def item_links(self, notification):
        return [{"href" : self.item_id(notification)}]
    
    def item_authors(self, notification):
        return [{"name" : notification.user.username}]


class NoticeUserFeed(BaseNoticeFeed):
    def get_object(self, params):
        return get_object_or_404(User, username=params[0].lower())

    def feed_id(self, user):
        return "%s://%s%s" % (
            DEFAULT_HTTP_PROTOCOL,
            Site.objects.get_current().domain,
            reverse('notification_feed_for_user'),
        )

    def feed_title(self, user):
        return _('Notices Feed')

    def feed_updated(self, user):
        qs = Notice.objects.filter(user=user)
        # We return an arbitrary date if there are no results, because there
        # must be a feed_updated field as per the Atom specifications, however
        # there is no real data to go by, and an arbitrary date can be static.
        if qs.count() == 0:
            return datetime(year=2008, month=7, day=1)
        return qs.latest('added').added

    def feed_links(self, user):
        complete_url = "%s://%s%s" % (
            DEFAULT_HTTP_PROTOCOL,
            Site.objects.get_current().domain,
            reverse('notification_notices'),
        )
        return ({'href': complete_url},)

    def items(self, user):
        return Notice.objects.notices_for(user).order_by("-added")[:ITEMS_PER_FEED]

class UserFeed(Feed):
    def get_object(self, request, username, url='feed/admin'):
        if not username:
            raise ObjectDoesNotExist
        return get_object_or_404(User, username__exact=username)

    def title(self, obj):
        return _("Recent activities by %(user)s" % {'user': obj.username })

    def description(self, obj):
        return _("Recent activities by user %s."%obj.username)

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return reverse('profile_public', args=[obj.username])

    def items(self, obj):
        return LogEntry.objects.by_user_and_public_projects(obj)

    def item_title(self, item):
        return _(item.action_type.display + ' ' + timesince(item.action_time) + ' ago.')

    def item_link(self, item):
        if not item:
            raise LogEntry.DoesNotExist
        if item.message:
            match = re.search(r'href=[\'"]?([^\'" >]+)', item.message)
            if match:
                return match.group(1)
            else:
                return '/'
        else:
            return '/'

    def item_description(self, item):
        return _(item.message or 'None')

