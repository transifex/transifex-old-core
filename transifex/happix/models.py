# -*- coding: utf-8 -*-
"""
String Level models.
"""
import datetime, hashlib, sys

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from languages.models import Language
from projects.models import Project
from txcommon.log import logger

# State Codes for translations
TRANSLATION_STATE_CHOICES = (
    ('APR', 'Approved'),
    ('FUZ', 'Fuzzy'),
    ('REJ', 'Rejected'),
)


# CORE
##############################################################

class TResourceManager(models.Manager):

    def create_or_update_from_file(self, path_to_file, project, 
                                   source_language=None,
                                   name=None, format='gettext'):
        """
        Wrapper to choose between create_from_file or TResource.update_from_file.
        """
        if not name:
            name = path_to_file
        #TODO: Language instantation should be based on caching
        # If None get the default which is english language instance.
        if not source_language:
            source_language = Language.objects.by_code_or_alias('en')

        try:
            tres = self.get(name=name, path=path_to_file, project=project, 
                            source_language=source_language)
            tres.update_from_file(path_to_file, format)
        except TResource.DoesNotExist:
            tres = self.create_from_file(name=name, path_to_file=path_to_file,
                                         project=project,
                                         source_language=source_language)
        return tres

    def create_from_file(self, path_to_file, project, source_language=None,
                         name=None, format='gettext'):
        """
        Create a TResource based on a provided source file and put the 
        source strings in the db by using the appropriate loaders.
        
        Return the TResource instance that is going to be loaded.
        """
        # To avoid circular referencing
        from happix.loaders import load_source_file

        if not name:
            name = path_to_file
        #TODO: Language instantation should be based on caching
        # If None get the default which is english language instance.
        if not source_language:
            source_language = Language.objects.by_code_or_alias('en')

        # Create the resource instance.
        tres = TResource.objects.create(name=name,
                                        path=path_to_file,
                                        project=project, 
                                        source_language=source_language)

        # Load the file to the DB and return the TResource instace.
        return load_source_file(path_to_file, tres, source_language, format)


class TResource(models.Model):
    """
    A translation resource, equivalent to a POT file, YAML file, string stream etc.
    
    The TResource points to a source language (template) file path! For example,
    it should be pointing to a .pot file or to a english .po file.of a project
    with english as the source language.
    The path_to_file should be point to :
        1. the relative path of the pot/source file in the vcs folder hierarchy
        2. an absolute URL (not local) to the file.
    The path_to_file should be used for loading (pull) operations!
    """
    name = models.CharField(_('Name'), max_length=255, null=False,
        blank=False, 
        help_text=_('A descriptive name unique inside the project.'))
    # URI, filepath etc.
    # FOR FILES: this should be the path to the source file (if pot exists) or
    # a parent folder path of the source language file.
    path = models.CharField(_('Path'), max_length=255, null=False,
        blank=False, 
        help_text=_("A path to the template file or to the source stream "
                    "inside the project folders hierarchy or a URI."))
    # Short identifier to be used in the API URLs
#    slug = models.SlugField(_('Slug'), max_length=50,
#        help_text=_('A short label to be used in the URL, containing only '
#                    'letters, numbers, underscores or hyphens.'))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    project = models.ForeignKey(Project, verbose_name=_('Project'),
        blank=False, null=True,
        help_text=_("The project which owns the translation resource."))
    source_language = models.ForeignKey(Language,
        verbose_name=_('Source Language'),blank=False, null=True,
        help_text=_("The source language of the translation resource."))

    # Managers
    objects = TResourceManager()

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = (('name', 'project'), 
                           #('slug', 'project'),
                           ('path', 'project'))
        verbose_name = _('tresource')
        verbose_name_plural = _('tresources')
        ordering  = ['name',]
        order_with_respect_to = 'project'
        get_latest_by = 'created'

    def update_from_file(self, path_to_file=None, format='gettext'):
        """
        Update the SourceStrings of the specific TResource based on file content.
        
        Returns the TResource instance.
        """
        # To avoid circular referrencing
        from happix.loaders import load_source_file

        # Reset the positions which are currently put.
        SourceString.objects.filter(tresource=self,
            language=self.source_language,).update(position=None)

        # Load the DB and return the instace.
        return load_source_file(path_to_file, self, self.source_language, format)

    def update_translations(self, path_to_file, target_language, format='gettext'):
        """
        Fetch the translations file and update the existing translations of the
        TResource for the target language
        """
        # To avoid circular referrencing
        from happix.loaders import load_translation_file
        try:
            tlanguage = Language.objects.by_code_or_alias(target_language)
            return load_translation_file(path_to_file, self, tlanguage,
                                         self.source_language, format)
        except Language.DoesNotExist:
            logger.warning("No Language exists with code or alias %s" % (target_language))

    def translated_strings(self, language):
        """
        Return the QuerySet of source strings, translated in this language.
        """
        target_language = Language.objects.by_code_or_alias(language)
        return SourceString.objects.filter(
                    tresource=self, 
                    position__isnull=False,
                    translationstring__language=target_language)

    def untranslated_strings(self, language):
        """
        Return the QuerySet of source strings which are not yet translated in
        the specific language.
        """
        target_language = Language.objects.by_code_or_alias(language)
        return SourceString.objects.filter(
                    tresource=self, 
                    position__isnull=False,).exclude(
                            translationstring__language=target_language)


class SourceString(models.Model):
    """
    A representation of a source string which is translated in many languages.
    
    The SourceString is pointing to a specific TResource and it is uniquely 
    defined by the string, description and tresource fields (so they are unique
    together).
    """

    string = models.CharField(_('String'), max_length=255,
        blank=False, null=False,
        help_text=_("The actual string content of source string."))
    description = models.CharField(_('Description'), max_length=255,
        blank=False, null=False,
        help_text=_("A description of the source string. This field specifies"
                    "the context of the source string inside the tresource."))
    position = models.IntegerField(_('Position'), blank=True, null=True,
        help_text=_("The position of the source string in the TResource."
                    "For example, the specific position of msgid field in a "
                    "po template (.pot) file in gettext."))
    #TODO: Decision for the following
    occurrences = models.TextField(_('Occurrences'), max_length=1000,
        blank=True, editable=False,
        help_text=_("The occurrences of the source string in the project code."))
    flags = models.TextField(_('Flags'), max_length=100,
        blank=True, editable=False,
        help_text=_("The flags which mark the source string. For example, if"
                    "there is a python formatted string this is marked as "
                    "\"#, python-format\" in gettext."))
    developer_comment = models.TextField(_('Flags'), max_length=1000,
        blank=True, editable=False,
        help_text=_("The comment of the developer."))
    #TODO: Decide if this field should be separated to a table to support more plurals.
    plural = models.CharField(_('Plural'), max_length=255,
        blank=True, editable=False,
        help_text=_("The plural form of the source string."))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    # A source string must always belong to a tresource
    tresource = models.ForeignKey(TResource, verbose_name=_('TResource'),
        blank=False, null=False,
        help_text=_("The translation resource which owns the source string."))
    language = models.ForeignKey(Language,
        verbose_name=_('Source Language'),blank=False, null=True,
        help_text=_("The source language of the translation resource."))

    #TODO: Managers
#    factory = SourceStringFactory()

    def __unicode__(self):
        return self.string

    class Meta:
        unique_together = (('string', 'description', 'tresource'),)
        verbose_name = _('source string')
        verbose_name_plural = _('source strings')
        ordering = ['string', 'description']
        order_with_respect_to = 'tresource'
        get_latest_by = 'created'


class SearchStringManager(models.Manager):
    def by_source_string_and_language(self, string,
            source_code='en', target_code=None):
        """
        Return the results of searching, based on a specific source string and
        maybe on specific source and/or target language.
        """
        source_strings = []
        # If the source language has not been provided, search strings for 
        # every source language.
        if source_code:
            source_language = Language.objects.by_code_or_alias(source_code)
            source_strings = SourceString.objects.filter(string=string,
                                                     language=source_language)
        else:
            source_strings = SourceString.objects.filter(string=string,)
        # If no target language given search on any target language.
        if target_code:
            language = Language.objects.by_code_or_alias(target_code)
            results = self.filter(
                        source_string__in=source_strings, language=language)
        else:
            results = self.filter(source_string__in=source_strings)
        return results


class TranslationString(models.Model):
    """
    The representation of a live translation for a given source string.
    
    This model encapsulates all the necessary fields for the translation of a 
    source string in a specific target language. It also contains a set of meta
    fields for the context of this translation.
    """

    string = models.CharField(_('String'), max_length=255,
        blank=False, null=False,
        help_text=_("The actual string content of translation."))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    # A source string must always belong to a tresource
    source_string = models.ForeignKey(SourceString,
        verbose_name=_('Source String'),
        blank=False, null=False,
        help_text=_("The source string which is being translated by this"
                    "translation string instance."))
    language = models.ForeignKey(Language,
        verbose_name=_('Target Language'),blank=False, null=True,
        help_text=_("The language in which this translation string belongs to."))
    user = models.ForeignKey(User,
        verbose_name=_('Committer'), blank=False, null=True,
        help_text=_("The user who committed the specific translation."))

    #TODO: Managers
    objects = SearchStringManager()

    def __unicode__(self):
        return self.string

    class Meta:
        unique_together = (('source_string', 'string', 'language'),)
        verbose_name = _('translation string')
        verbose_name_plural = _('translation strings')
        ordering  = ['string',]
        order_with_respect_to = 'source_string'
        get_latest_by = 'created'


#TODO: Consider and decide if we should merge it with TranslationString 
# (index field is the only one needed)
class PluralTranslationString(models.Model):
    """
    This table holds the plural statements of every translation string 
    on specific source strings.
    
    The plural translation is pointing to the source string because there may be
    cases where a singular form translation string may not exist, but a plural
    string exists. Both of them should point to the correct source string which
    is being translated.
    In order to permit lookups based on number of plurals for each language, we
    provide an index similar to the one Gettext is using.
    """

    string = models.CharField(_('String'), max_length=255,
        blank=False, null=False,
        help_text=_("The actual string content of plural translation."))
    index = models.IntegerField(_('Index'), blank=False, null=False,
        help_text=_("The position of the plural string in the list of plurals."))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    source_string = models.ForeignKey(SourceString,
        verbose_name=_('Source String'),
        blank=False, null=False,
        help_text=_("The source string which is being translated by this"
                    "plural translation string instance."))
    language = models.ForeignKey(Language,
        verbose_name=_('Target Language'),blank=False, null=True,
        help_text=_("The language in which this translation string belongs to."))

    def __unicode__(self):
        return self.string

    class Meta:
        unique_together = (('source_string', 'string', 'language', 'index'),)
        verbose_name = _('plural translation string')
        verbose_name_plural = _('plural translation strings')
        ordering  = ['source_string', 'index']
        get_latest_by = 'created'


class TranslationSuggestion(models.Model):
    """
    A suggestion for the translation of a specific source string in a language.

    Suggestions are used as hints to the committers of the original translations.
    A fuzzy translation string is also put here as a suggestion. Suggestions
    can also be used (if it is chosen) to give non-team members the chance
    to suggest a translation on a source string, permitting anonymous or
    arbitrary logged in user translation.
    Suggestions have a score which can be increased or decreased by users,
    indicating how good is the translation of the source string.
    The best translation could be automatically chosen as a live 
    TranslationString by using a heuristic.
    """

    string = models.CharField(_('String'), max_length=255,
        blank=False, null=False,
        help_text=_("The actual string content of translation."))
    score = models.FloatField(_('Score'), blank=True, null=True, default=0,
        help_text=_("A value which indicates the relevance of this translation."))
    live = models.BooleanField(_('Live'), default=False, editable=False)

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    # A source string must always belong to a tresource
    source_string = models.ForeignKey(SourceString,
        verbose_name=_('Source String'),
        blank=False, null=False,
        help_text=_("The source string which is being translated by this"
                    "suggestion instance."))
    language = models.ForeignKey(Language,
        verbose_name=_('Target Language'),blank=False, null=True,
        help_text=_("The language in which this translation string belongs to."))
    user = models.ForeignKey(User,
        verbose_name=_('Committer'), blank=False, null=True,
        help_text=_("The user who committed the specific suggestion."))

    #TODO: Managers

    def __unicode__(self):
        return self.string

    class Meta:
        # Only one suggestion can be committed by each user for a source_string 
        # in a specific language!
        unique_together = (('source_string', 'string', 'language'),)
        verbose_name = _('translation suggestion')
        verbose_name_plural = _('translation suggestions')
        ordering  = ['string',]
        order_with_respect_to = 'source_string'
        get_latest_by = 'created'
