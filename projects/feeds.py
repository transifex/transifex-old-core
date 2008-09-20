from django.contrib.syndication.feeds import Feed
from django.utils.translation import ugettext_lazy as _
from projects.models import Project

class LatestProjects(Feed):
    title = _("Transifex website")
    link = "http://transifex.com/"
    description = _("Updates on changes and additions to projects.")

    def items(self):
        return Project.objects.order_by('-created')[:5]
