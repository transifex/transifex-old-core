from django.contrib.syndication.feeds import Feed
from django.utils.translation import ugettext_lazy as _
from models import Language

class AllLanguages(Feed):
    title = _("Transifex languages")
    # FIXME: get this from sites and settings.py
    link = "http://transifex.net/"
    description = _("The languages Transifex speaks.")

    def items(self):
        return Language.objects.all()
