from datetime import datetime
from django.contrib import admin
from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from languages.models import Language

class POFileManager(models.Manager):
    def get_for_object(self, obj):
        """
        Create a queryset matching all POFiles associated with the given
        object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(content_type__pk=ctype.pk,
                           object_id=obj.pk)

class POFile(models.Model):
    """
    A POFile is a collection of information about translations stats
    of a component in a language.
    
    """    
    total = models.PositiveIntegerField(default=0)
    trans = models.PositiveIntegerField(default=0)
    fuzzy = models.PositiveIntegerField(default=0)
    untrans = models.PositiveIntegerField(default=0)

    trans_perc = models.PositiveIntegerField(default=0, editable=False)
    fuzzy_perc = models.PositiveIntegerField(default=0, editable=False)
    untrans_perc = models.PositiveIntegerField(default=100, editable=False)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')
    
    lang = models.ForeignKey(Language, null=True)
    filename = models.TextField(null=False, max_length=1000)

    enabled = models.BooleanField(default=True)
    created = models.DateField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    objects = POFileManager()

    def __unicode__(self):
        return u"%(file)s (%(type)s %(obj)s)" % {
            'file': self.filename,
            'type': self.content_type,
            'obj': self.object,}

    class Meta:
        verbose_name = _('PO file')
        verbose_name_plural = _('PO files')
        db_table  = 'translations_pofile'
        ordering  = ('filename', 'lang')
        
    def save(self, *args, **kwargs):
        self.modified = datetime.now()
        super(POFile, self).save(*args, **kwargs)

    def calulate_perc(self):
        if self.total != 0:
            self.trans_perc = self.trans*100/self.total
            self.fuzzy_perc = self.fuzzy*100/self.total
            self.untrans_perc = self.untrans*100/self.total
        else:
            self.trans_perc = 0
            self.fuzzy_perc = 0
            self.untrans_perc = 100
        
    def set_stats(self, trans=0, fuzzy=0, untrans=0):
        """ Initialize the object"""
        self.total = trans + fuzzy + untrans
        self.trans = trans
        self.fuzzy = fuzzy
        self.untrans = untrans
        self.calulate_perc()

    @classmethod
    def stats_for_lang(self, lang):
        """ Returns a list of objects statistics for a language."""
        return self.objects.filter(lang=lang).order_by('-trans_perc')

def suite():
    """
    Define the testing suite for Django's test runner.
    
    Enables test execution with ``./manage.py test <appname>``.
    """
     
    import unittest
    import doctest
    s = unittest.TestSuite()

    #FIXME: Load tests automatically:
    #    for vcs_type in settings.VCS_CHOICES:
    #        vcs_browser = import_to_python('vcs.lib.types' % vcs_type)
    #        s.addTest(doctest.DocTestSuite(vcs_browser))
    from translations.tests import test_models 
    s.addTest(doctest.DocTestSuite(test_models))
        
    return s
