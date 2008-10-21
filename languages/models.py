from datetime import datetime
from django.contrib import admin
from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class Language(models.Model):

    """
    A Language is a code and name collection of languages.
    """

    name = models.CharField(unique=True, max_length=50,
        help_text="The name of the language including dialect, script, etc.")
    code = models.CharField(unique=True, max_length=50,
        help_text=("The primary language code, used in file naming, etc."
                   "(eg. pt_BR for Brazilian Portuguese.)"))
    code_aliases = models.CharField(max_length=100,
        help_text=("A space-separated list of alternative locales."),
        null=True, default='')

    class Meta:
        verbose_name = _('language')
        verbose_name_plural = _('languages')
        db_table  = 'translations_language'
        ordering  = ('name',)

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.code)

    @permalink
    def get_absolute_url(self):
        return ('language_detail', None, { 'slug': self.code })


def suite():
    """Define this application's testing suite for Django's test runner."""
     
    import unittest
    import doctest
    from languages.tests import test_models 

    s = unittest.TestSuite()
    s.addTest(doctest.DocTestSuite(test_models))
    return s