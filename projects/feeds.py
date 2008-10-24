from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.syndication.feeds import Feed
from django.contrib.sites.models import Site
from projects.models import Project


class LatestProjects(Feed):
    current_site = Site.objects.get_current()
    title = _("Latest projects on %(site_name)s") % {
        'site_name': current_site.name }
    link = current_site.domain
    description = _("Updates on changes and additions to registered projects.")

    def items(self):
        return Project.objects.order_by('-created')[:10]
