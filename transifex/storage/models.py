# -*- coding: utf-8 -*-
import datetime, hashlib, sys
from django.db.models import permalink
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

#from happix.models import PARSERS
from languages.models import Language
from projects.models import Project
from txcommon.log import logger

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
        help_text=_("The language in which this translation string belongs to."))

    #resource = models.ForeignKey(Resource, verbose_name=_('Resource'),
        #blank=False, null=True,
        #help_text=_("The translation resource which owns the source string."))

#    project = models.ForeignKey(Project, verbose_name=_('Project'), blank=False, null=True)

    bound = models.BooleanField(verbose_name=_('Bound to any object'), default=False,
        help_text=_('Wether this file is bound to a project/translation resource, otherwise show in the upload box'))

    user = models.ForeignKey(User,
        verbose_name=_('Owner'), blank=False, null=True,
        help_text=_("The user who uploaded the specific file."))
    
    created = models.DateTimeField(auto_now_add=True, editable=False)
    total_strings = models.IntegerField(_('Total number of strings'), blank=True, null=True)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.uuid)

    def get_storage_path(self):
        return "/tmp/%s-%s" % (self.uuid, self.name)

    def translatable(self):
        """
        Wether we could extract any strings -> wether we can translate file
        """
        return (self.total_strings > 0)

    def update_props(self):
        """
        Try to parse the file and fill in information fields in current model
        """
        pass
        #FIXME: Decide whether it's important to have it and find a good way 
        # to import the PARSERS.

        #parser = None
        #for p in PARSERS:
            #if p.accept(self.name):
                #parser = p
                #break

        #if not parser:
            #return

        #self.mime_type = parser.mime_type

        #stringset = parser.parse_file(self.get_storage_path())
        #if not stringset:
            #return

        #if stringset.target_language:
            #try:
                #self.language = Language.objects.by_code_or_alias(stringset.target_language)
            #except Language.DoesNotExist:
                #pass

        #self.total_strings = len([s for s in stringset.strings if s.rule==5])
        #return