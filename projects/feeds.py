from django.contrib.syndication.feeds import Feed
from models import Project

class LatestProjects(Feed):
    title = "Transifex website"
    link = "http://transifex.com/"
    description = "Updates on changes and additions to projects."

    def items(self):
        return Project.objects.order_by('-created')[:5]
