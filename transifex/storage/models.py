# -*- coding: utf-8 -*-
import os
import datetime, hashlib, sys
from django.conf import settings
from django.db.models import permalink
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from transifex.languages.models import Language
from transifex.txcommon.exceptions import FileCheckError
from transifex.txcommon.log import logger

import magic

class StorageFile(models.Model):
    """
    StorageFile refers to a uploaded file. Initially
    """
    # File name of the uploaded file
    name = models.CharField(max_length=1024)
    size = models.IntegerField(_('File size in bytes'), blank=True, null=True)
    mime_type = models.CharField(max_length=255)

    # Path for storage
    uuid = models.CharField(max_length=1024)

    # Foreign Keys
    language = models.ForeignKey(Language,
        verbose_name=_('Source language'),blank=False, null=True,
        help_text=_("The language in which this translation string is written."))

    #resource = models.ForeignKey(Resource, verbose_name=_('Resource'),
        #blank=False, null=True,
        #help_text=_("The translation resource which owns the source string."))

#    project = models.ForeignKey(Project, verbose_name=_('Project'), blank=False, null=True)

    bound = models.BooleanField(verbose_name=_('Bound to any object'), default=False,
        help_text=_('Whether this file is bound to a project/translation resource, otherwise show in the upload box'))

    user = models.ForeignKey(User,
        verbose_name=_('Owner'), blank=False, null=True,
        help_text=_("The user who uploaded the specific file."))

    created = models.DateTimeField(auto_now_add=True, editable=False)
    total_strings = models.IntegerField(_('Total number of strings'), blank=True, null=True)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.uuid)

    def delete(self, *args, **kwargs):
        """
        Delete file from filesystem even if object has not been saved yet.
        """
        try:
            os.remove(self.get_storage_path())
        except OSError, e:
            if self.id:
                logger.debug("Error deleting StorageFile: %s" % str(e))
        if self.id:
            super(StorageFile, self).delete(*args, **kwargs)

    def get_storage_path(self):
        filename = "%s-%s" % (self.uuid, self.name)
        return os.path.join(settings.STORAGE_DIR, filename)

    def translatable(self):
        """
        Whether we could extract any strings -> whether we can translate file
        """
        return (self.total_strings > 0)

    def find_parser(self):
        #FIXME: Decide whether it's important to have it and find a good way
        # to import the PARSERS.
        from transifex.resources.parsers import PARSERS
        parser = None
        for p in PARSERS:
            if p.accepts(filename=self.name,mime=self.mime_type):
                parser = p
                break

        return parser

    def file_check(self):
        """
        Check whether the uploaded file if valid.

        Run a number of checks on the StorageFile contents, including specific
        checks, depending on the i18n format of the file.
        """
        # Get appropriate parser
        parser = self.find_parser()

        if not parser:
            logger.debug("file: File is not supported.")
            raise FileCheckError(ugettext("File you are trying to upload does not "
                "seem to belong to a known i18n format."))

        # Empty file check
        if self.size == 0:
            logger.debug("file: Empty file!")
            raise FileCheckError(ugettext("You have uploaded an empty file!"))

        # Specific check for the i18n format
        parser.contents_check(self.get_storage_path())


    def update_props(self):
        """
        Try to parse the file and fill in information fields in current model
        """
        # this try to guess the API of the magic module, between
        # the one from file and the other one from python-magic
        try:
                m = magic.Magic(mime=True)
                # guess mimetype and remove charset
                self.mime_type = m.from_file(self.get_storage_path())
        except AttributeError:
                m = magic.open(magic.MAGIC_NONE)
                m.load()
                self.mime_type = m.file(self.get_storage_path())
                m.close()

        self.save()

        parser = self.find_parser()

        if not parser:
            return

        fpo = parser(filename = self.get_storage_path() )
        fpo.set_language(self.language)
        fpo.contents_check(self.get_storage_path())
        fpo.parse_file()

        stringset = fpo.stringset
        if not stringset:
            return

        if stringset.target_language:
            try:
                self.language = Language.objects.by_code_or_alias(stringset.target_language)
            except Language.DoesNotExist:
                pass

        self.total_strings = len([s for s in stringset.strings if s.rule==5])
        return
