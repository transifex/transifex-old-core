from datetime import datetime
from django.contrib import admin
from django.db import models
from django.db.models import permalink, get_model
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

    def by_code_or_alias_or_none(self, code):
        """
        Return a language that matches either with the code or something
        inside the code_aliases field. If no match is found return None.
        """
        try:
            return self.by_code_or_alias(code)
        except Language.DoesNotExist:
            return None

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

    # Plural rules
    rule_zero = models.CharField(_("Rule zero"), max_length=255,
        blank=True, null=True)
    rule_one = models.CharField(_("Rule one"), max_length=255,
        blank=True, null=True)
    rule_two = models.CharField(_("Rule two"), max_length=255,
        blank=True, null=True)
    rule_few = models.CharField(_("Rule few"), max_length=255,
        blank=True, null=True)
    rule_many = models.CharField(_("Rule many"), max_length=255,
        blank=True, null=True)
    rule_other = models.CharField(_("Rule other"), max_length=255,
        blank=False, null=False, default="everything")


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

    def get_rule_name_from_num(self, num):
        if num == 0:
            return 'zero'
        elif num == 1:
            return 'one'
        elif num == 2:
            return 'two'
        elif num == 3:
            return 'few'
        elif num == 4:
            return 'many'
        elif num == 5:
            return 'other'

    def get_rule_num_from_name(self, name):
        if name == 'zero':
            return 0
        elif name == 'one':
            return 1
        elif name == 'two':
            return 2
        elif name == 'few':
            return 3
        elif name == 'many':
            return 4
        elif name == 'other':
            return 5

    def get_pluralrules(self):
        rules=[]
        if self.rule_zero:
            rules.append('zero')
        if self.rule_one:
            rules.append('one')
        if self.rule_two:
            rules.append('two')
        if self.rule_few:
            rules.append('few')
        if self.rule_many:
            rules.append('many')
        rules.append('other')
        return rules

    def get_pluralrules_numbers(self):
        rules=[]
        if self.rule_zero:
            rules.append(0)
        if self.rule_one:
            rules.append(1)
        if self.rule_two:
            rules.append(2)
        if self.rule_few:
            rules.append(3)
        if self.rule_many:
            rules.append(4)
        rules.append(5)
        return rules

    def translated_strings(self):
        """
        Return the QuerySet of source entities, translated in this language.
        
        This assumes that we DO NOT SAVE empty strings for untranslated entities!
        """
        # I put it here due to circular dependency on modules
        from happix.models import SourceEntity, Translation
        return SourceEntity.objects.filter(id__in=Translation.objects.filter(
                language=self, rule=5).values_list('source_entity', flat=True))

    def untranslated_strings(self):
        """
        Return the QuerySet of source entities which are not yet translated in
        the specific language.
        
        This assumes that we DO NOT SAVE empty strings for untranslated entities!
        """
        # I put it here due to circular dependency on modules
        from happix.models import SourceEntity, Translation
        return SourceEntity.objects.exclude(id__in=Translation.objects.filter(
                language=self, rule=5).values_list('source_entity', flat=True))

    def num_translated(self):
        """
        Return the number of translated strings in all Resources for the language.
        """
        return self.translated_strings().count()

    def num_untranslated(self):
        """
        Return the number of untranslated strings in all Resources for the language.
        """
        return self.untranslated_strings().count()

    def trans_percent(self):
        """Return the percent of untranslated strings in all Resources."""
        # Import here due to circular dependency on modules
        from happix.models import SourceEntity
        #TODO:We need this as a cached value in order to avoid hitting the db all the time
        total_entities = SourceEntity.objects.count()
        t = self.num_translated()
        try:
            return (t * 100 / total_entities)
        except ZeroDivisionError:
            return 100

    def untrans_percent(self):
        """Return the percent of untranslated strings in this Resource."""
        translated_percent = self.trans_percent()
        return (100 - translated_percent)

def suite():
    """Define this application's testing suite for Django's test runner."""
     
    import unittest
    import doctest
    from languages.tests import test_models 

    s = unittest.TestSuite()
    s.addTest(doctest.DocTestSuite(test_models))
    return s
