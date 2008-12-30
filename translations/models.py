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

    def by_language(self, language):
        """ Returns a list of objects statistics for a language."""
        return self.filter(language=language).order_by('-trans_perc')
    
    
class POFile(models.Model):
    """
    A POFile is a representation of a PO file structure.
    
    It can either be a real PO file on a repository, a
    dynamically-generated one, etc. It represents the translation
    of a component to a language. The model's basic use is the
    calculation of translation statistics.    
    """

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')
    
    total = models.PositiveIntegerField(default=0)
    trans = models.PositiveIntegerField(default=0)
    fuzzy = models.PositiveIntegerField(default=0)
    untrans = models.PositiveIntegerField(default=0)
    
    language = models.ForeignKey(Language, null=True)
    filename = models.TextField(null=False, max_length=1000)

    enabled = models.BooleanField(default=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    error = models.BooleanField(default=False, editable=False)
    
    # Normalized fields
    trans_perc = models.PositiveIntegerField(default=0, editable=False)
    fuzzy_perc = models.PositiveIntegerField(default=0, editable=False)
    untrans_perc = models.PositiveIntegerField(default=100, editable=False)

    # Managers
    objects = POFileManager()

    def __unicode__(self):
        return u"%(file)s (%(type)s %(obj)s)" % {
            'file': self.filename,
            'type': self.content_type,
            'obj': self.object,}

    class Meta:
        unique_together = ("content_type", "object_id", "filename")
        verbose_name = _('PO file')
        verbose_name_plural = _('PO files')
        db_table  = 'translations_pofile'
        ordering  = ('filename', 'language')
        get_latest_by = 'created'
        
    def save(self, *args, **kwargs):
        self.calculate_perc()
        super(POFile, self).save(*args, **kwargs)

    def calculate_perc(self):
        """Update normalized percentage statistics fields."""
        try:
            self.trans_perc = self.trans * 100 / self.total
            self.fuzzy_perc = self.fuzzy * 100 / self.total
            self.untrans_perc = self.untrans * 100 / self.total
        except ZeroDivisionError:
            self.trans_perc = 0
            self.fuzzy_perc = 0
            self.untrans_perc = 0

    def set_stats(self, trans=0, fuzzy=0, untrans=0, error=False):
        self.total = trans + fuzzy + untrans
        self.trans = trans
        self.fuzzy = fuzzy
        self.untrans = untrans
        self.error = error
        self.calculate_perc()
    
    def guess_lang(self):
        """
        Try to find the language of the POFile.

        Return None if guesswork fails.
        This method is currently specific to <lang>.po files.        
        """
        # FIXME: Per-i18n-type functionality is stroed in the transmanager,
        # and this method should be there. Or, we should have this model
        # tied to a particular manager. Design decision needed.

        from os.path import basename
        try:
            lang_code = basename(self.filename[:-3:])
            return Language.objects.get(code=lang_code)
        except:
            return


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
