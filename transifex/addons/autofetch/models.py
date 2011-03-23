from django.db import models
from django.utils.translation import ugettext_lazy as _

from transifex.resources.models import Resource
from transifex.txcommon.log import logger
from transifex.resources.formats import (get_i18n_handler_from_type,
    get_i18n_type_from_file)

import os
import urllib2, urlparse
from uuid import uuid4

StorageFile = models.get_model("storage", "StorageFile")

class URLInfo(models.Model):

   # URL info for remote fetching/updating
    source_file_url = models.URLField(_('Source file URL'),
        null=True, blank=True, verify_exists=True,
        help_text=_("A URL pointing to the source file of this resource"\
            " to be used for automatic updates."))
    auto_update = models.BooleanField(_("Automatically update source file"),
        default=False, help_text=_("A boolean field indicating whether the"\
        " file should be automatically updated by pulling and merging from"\
        " the given URL."))

    # Foreign keys
    resource = models.OneToOneField(Resource, verbose_name=_('Resource'),
        blank=False, null=False, related_name='url_info', unique=True,
        help_text=_("The translation resource."))

    class Meta:
        verbose_name = _('url handler')
        ordering  = ('resource',)

    def __unicode__(self):
        return "%s.%s" % (self.resource.project.slug, self.resource.slug)

    def update_source_file(self, fake=False):
        """
        Fetch source file from remote url and import it, updating existing
        entries.
        """
        try:
            file = urllib2.urlopen(self.source_file_url)
        except:
            logger.error("Could not pull source file for resource %s (%s)" %
                (self.resource.full_name, self.source_file_url))
            raise

        filename = ''
        if file.info().has_key('Content-Disposition'):
                # If the response has Content-Disposition, we try to take
                # filename from it
                content = file.info()['Content-Disposition']
                if 'filename' in content:
                    filename = content.split('filename')[1]
                    filename = filename.replace('"', '').replace("'", ""
                        ).replace("=", "").replace('/', '-').strip()

        if filename == '':
            parts = urlparse.urlsplit(self.source_file_url)
            #FIXME: This still might end empty
            filename = parts.path.split('/')[-1]

        sf = StorageFile()
        sf.uuid = str(uuid4())
        sf.name = filename
        fh = open(sf.get_storage_path(), 'wb')
        fh.write(file.read())
        fh.flush()
        fh.close()

        sf.size = os.path.getsize(sf.get_storage_path())
        sf.language = self.resource.source_language

        sf.update_props()
        sf.save()

        try:
            if self.resource.i18n_type:
                parser = get_i18n_handler_from_type(self.resource.i18n_type)
            else:
                parser = sf.find_parser()
                assert parser, "Could not find a suitable handler for this file."
                i18n_type = get_i18n_type_from_file(sf.get_storage_path())
                self.resource.i18n_type = i18n_type
                self.resource.save()
            language = sf.language
            fhandler = parser(filename=sf.get_storage_path())
            fhandler.set_language(language)
            fhandler.bind_resource(self.resource)
            fhandler.contents_check(fhandler.filename)
            fhandler.parse_file(is_source=True)
            strings_added, strings_updated = 0, 0
            if not fake:
                strings_added, strings_updated = fhandler.save2db(is_source=True)
        except Exception,e:
            logger.error("Error importing source file for resource %s.%s (%s): %s" %
                ( self.resource.project.slug, self.resource.slug,
                    self.source_file_url, str(e)))
            raise

        return strings_added, strings_updated
