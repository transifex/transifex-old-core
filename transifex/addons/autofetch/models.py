from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.http import HttpRequest

from transifex.resources.models import Resource

import os
import urllib2
from uuid import uuid4
import simplejson as json

StorageFile = models.get_model("storage", "StorageFile")

class URLInfo(models.Model):

   # URL info for remote fetching/updating
    source_file_url = models.URLField(_('Source file URL'), 
        null=True, blank=True, verify_exists=True,
        help_text=_("A URL pointing to the source file of this resource"\
            " which can be used for auto updating."))
    auto_update = models.BooleanField(_("Auto update source file"), 
        default=False, help_text=_("A boolean field representing whether we"\
        " should periodically pull and merge the source file for the given"\
        " URL."))

    # Foreign keys
    resource = models.ForeignKey(Resource, verbose_name=_('Resource'),
        blank=False, null=False, related_name='url_info', unique=True,
        help_text=_("The translation resource."))

    class Meta:
        verbose_name = _('url handler')
        ordering  = ('resource',)

    def __unicode__(self):
        return "%s.%s" % (self.resource.project.slug, self.resource.slug)

    def update_source_file(self):
        """
        Fetch source file from remote url and import it, updating existing
        entries.
        """

        file = urllib2.urlopen(self.source_file_url)
        sf = StorageFile()
        sf.uuid = str(uuid4())
        fh = open(sf.get_storage_path(), 'wb')
        fh.write(file.read())
        fh.flush()
        fh.close()

        sf.size = os.path.getsize(sf.get_storage_path())
        sf.language = self.resource.source_language

        sf.update_props()
        sf.file_check()
        sf.save()

        parser = sf.find_parser()
        language = sf.language
        fhandler = parser(filename=sf.get_storage_path())
        fhandler.set_language(language)
        fhandler.bind_resource(self.resource)
        fhandler.contents_check(fhandler.filename)
        fhandler.parse_file()
        strings_added, strings_updated = fhandler.save2db()

        return strings_added, strings_updated
