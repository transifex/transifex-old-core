from datetime import datetime
from django.contrib import admin
from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class LanguageManager(models.Manager):
    def by_code_or_alias(self, code):        
        """
        Return a language that matches either with the code or something
        inside the code_aliases field.
        """
        return Language.objects.get(
            models.Q(code=code) |
            models.Q(code_aliases__contains=' %s ' % code))

class Language(models.Model):

    """
    A spoken language or dialect, with a distinct locale.
    """
    nplural_choices = ((0, u'unknown'), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6))

    name = models.CharField(_('Name'), unique=True, max_length=50,
        help_text="The name of the language including dialect, script, etc.")
    description = models.CharField(_('Description'), blank=True, max_length=255)
    code = models.CharField(_('Code'), unique=True, max_length=50,
        help_text=("The primary language code, used in file naming, etc."
                   "(eg. pt_BR for Brazilian Portuguese.)"))
    code_aliases = models.CharField(_('Code aliases'), max_length=100,
        help_text=("A space-separated list of alternative locales."),
        null=True, default='')
    specialchars = models.CharField(_("Special Chars"), max_length=255, 
        help_text=_("Enter any special characters that users might find"
                    " difficult to type"),
        blank=True)
    nplurals = models.SmallIntegerField(_("Number of Plurals"), default=0,
        choices=nplural_choices)
    pluralequation = models.CharField(_("Plural Equation"), max_length=255,
        blank=True)


    # Managers
    objects = LanguageManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.code)

    class Meta:
        verbose_name = _('language')
        verbose_name_plural = _('languages')
        db_table  = 'translations_language'
        ordering  = ('name',)

    @permalink
    def get_absolute_url(self):
        return ('language_detail', None, { 'slug': self.code })

    @property
    def components(self):
        from projects.models import Component
        return Component.objects.with_language(self)

    def save(self, *args, **kwargs):
        # It's needed to ensure that when we compare this field with the
        # 'contain' action, we will always take the whole alias for a 
        # language, instead of part of it. We compare the alias with spaces
        # at the beginning and at the end of it.
        # TODO: check if alias does not already exist
        if not self.code_aliases.startswith(' '):
            self.code_aliases=' %s' % self.code_aliases
        if not self.code_aliases.endswith(' '):
            self.code_aliases='%s ' % self.code_aliases

        super(Language, self).save(*args, **kwargs)

def suite():
    """Define this application's testing suite for Django's test runner."""
     
    import unittest
    import doctest
    from languages.tests import test_models 

    s = unittest.TestSuite()
    s.addTest(doctest.DocTestSuite(test_models))
    return s
