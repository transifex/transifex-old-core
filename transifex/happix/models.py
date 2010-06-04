# -*- coding: utf-8 -*-
"""
String Level models.
"""
import datetime, hashlib, sys
from django.db.models import permalink
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from languages.models import Language
from projects.models import Project
from txcommon.log import logger

def reset():
    Translation.objects.all().delete()
    StringSet.objects.all().delete()
    SourceEntity.objects.all().delete()

# State Codes for translations
TRANSLATION_STATE_CHOICES = (
    ('APR', 'Approved'),
    ('FUZ', 'Fuzzy'),
    ('REJ', 'Rejected'),
)

from django.db import transaction

"""
Parsers need to be somewhat rewritten, currently each one implements parse(buf) function which returns libtransifex.core.StringSet class,
and compile(stringset) which returns file buffer.

It actually makes more sense to store all uploaded files, parse only the information we are interested in, and during compilation,
take the uploaded file as template, and just replace modified parts
"""

from libtransifex.qt import LinguistParser # Qt4 TS files
from libtransifex.java import JavaPropertiesParser # Java .properties
from libtransifex.apple import AppleStringsParser # Apple .strings
#from libtransifex.ruby import YamlParser # Ruby On Rails (broken)
#from libtransifex.resx import ResXmlParser # Microsoft .NET (not finished)
from libtransifex.pofile import PofileParser # GNU Gettext .PO/.POT parser

PARSERS = [PofileParser, LinguistParser, JavaPropertiesParser, AppleStringsParser]

# For faster lookup
PARSER_MAPPING = {}
for parser in PARSERS:
    PARSER_MAPPING[parser.mime_type] = parser


class TResourceGroup(models.Model):
    """
    Model for grouping TResources.
    """
    # FIXME: add necessary fields
    pass


class TResourceManager(models.Manager):
    pass

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

    # Short identifier to be used in the API URLs
    slug = models.SlugField(_('Slug'), max_length=50,
        help_text=_('A short label to be used in the URL, containing only '
            'letters, numbers, underscores or hyphens.'))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    source_language = models.ForeignKey(Language,
        verbose_name=_('Source Language'),blank=False, null=False,
        help_text=_("The source language of this TResource."))

    project = models.ForeignKey(Project, verbose_name=_('Project'),
        blank=False,
        null=True,
        help_text=_("The project which owns the translation resource."))

    tresource_group = models.ForeignKey(TResourceGroup, verbose_name=_("TResource Group"),
        blank=False, null=True,
        help_text=_("A group under which TResources are organized."))

    # Managers
    objects = TResourceManager()

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = (('name', 'project'),)
                           #('slug', 'project'),
                           #('path', 'project'))
        verbose_name = _('tresource')
        verbose_name_plural = _('tresources')
        ordering  = ['name',]
        order_with_respect_to = 'project'
        get_latest_by = 'created'

    @permalink
    def get_absolute_url(self):
        return ('project.resource', None, { 'project_slug': self.project.slug, 'tresource_slug' : self.slug })


    def translated_strings(self, language):
        """
        Return the QuerySet of source strings, translated in this language.
        """
        target_language = Language.objects.by_code_or_alias(language)
        return SourceEntity.objects.filter(
                    tresource=self, 
                    position__isnull=False,
                    translationstring__language=target_language)

    def untranslated_strings(self, language):
        """
        Return the QuerySet of source strings which are not yet translated in
        the specific language.
        """
        target_language = Language.objects.by_code_or_alias(language)
        return SourceEntity.objects.filter(
                    tresource=self, 
                    position__isnull=False,).exclude(
                            translationstring__language=target_language)

    @transaction.commit_manually
    def merge_stringset(self, stringset, target_language, user=None, overwrite_translations=True):
        try:
            strings_added = 0
            strings_updated = 0
            for j in stringset.strings:
                # If is primary language update source strings!
                ss, created = SourceEntity.objects.get_or_create(
                    string= j.source_entity,
                    context=j.context or "None",
                    tresource=self,
                    defaults = {
                        'position' : 1,
                    }
                )
                ts, created = Translation.objects.get_or_create(
                    source_entity=ss,
                    language = target_language,
                    tresource = self,
                    defaults={
                        'string' : j.translation_string,
                        'user' : user,
                    },
                )

                if created:
                    strings_added += 1

                if not created and overwrite_translations:
                    if ts.string != j.translation_string:
                        ts.string = j.translation_string
                        strings_updated += 1
                        updated = True
        except:
            transaction.rollback()
            return 0,0
        else:
            transaction.commit()
            return strings_added, strings_updated

    def merge_translation_file(self, translation_file):
        stringset = PARSER_MAPPING[translation_file.mime_type].parse_file(filename = translation_file.get_storage_path())
        return self.merge_stringset(stringset, translation_file.language)

class SourceEntity(models.Model):
    """
    A representation of a source string which is translated in many languages.
    
    The SourceEntity is pointing to a specific TResource and it is uniquely 
    defined by the string, context and tresource fields (so they are unique
    together).
    """
    string = models.CharField(_('String'), max_length=255,
        blank=False, null=False,
        help_text=_("The actual string content of source string."))
    context = models.CharField(_('Context'), max_length=255,
        blank=False, null=False,
        help_text=_("A description of the source string. This field specifies"
                    "the context of the source string inside the tresource."))
    position = models.IntegerField(_('Position'), blank=True, null=True,
        help_text=_("The position of the source string in the TResource."
                    "For example, the specific position of msgid field in a "
                    "po template (.pot) file in gettext."))
    #TODO: Decision for the following
    occurrences = models.TextField(_('Occurrences'), max_length=1000,
        blank=True, editable=False, null=True,
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

    def __unicode__(self):
        return self.string

    class Meta:
#        unique_together = (('string', 'context', 'tresource'),)
        verbose_name = _('source string')
        verbose_name_plural = _('source strings')
        ordering = ['string', 'context']
        order_with_respect_to = 'tresource'
        get_latest_by = 'created'


class SearchStringManager(models.Manager):
    def by_source_entity_and_language(self, string,
            source_code='en', target_code=None):
        """
        Return the results of searching, based on a specific source string and
        maybe on specific source and/or target language.
        """
        source_entitys = []

        source_entitys = SourceEntity.objects.filter(string=string,)

        # If no target language given search on any target language.
        if target_code:
            language = Language.objects.by_code_or_alias(target_code)
            results = self.filter(
                        source_entity__in=source_entitys, language=language)
        else:
            results = self.filter(source_entity__in=source_entitys)
        return results


class Translation(models.Model):
    """
    The representation of a live translation for a given source string.
    
    This model encapsulates all the necessary fields for the translation of a 
    source string in a specific target language. It also contains a set of meta
    fields for the context of this translation.
    """

    string = models.CharField(_('String'), max_length=255,
        blank=False, null=False,
        help_text=_("The actual string content of translation."))

    number = models.IntegerField(_('Number'), blank=False,
         null=False, default=0,
        help_text=_("The number of the string. 0 for singular and 1,2,3,etc"
                    " for plural forms."))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    # A source string must always belong to a tresource
    source_entity = models.ForeignKey(SourceEntity,
        verbose_name=_('Source String'),
        blank=False, null=False,
        help_text=_("The source string which is being translated by this"
                    "translation string instance."))

    language = models.ForeignKey(Language,
        verbose_name=_('Target Language'),blank=False, null=True,
        help_text=_("The language in which this translation string belongs to."))

    # Foreign Keys
    # A source string must always belong to a tresource
    tresource = models.ForeignKey(TResource, verbose_name=_('TResource'),
        blank=False, null=False,
        help_text=_("The translation resource which owns the source string."))

    user = models.ForeignKey(User,
        verbose_name=_('Committer'), blank=False, null=True,
        help_text=_("The user who committed the specific translation."))

    #TODO: Managers
    objects = SearchStringManager()

    def __unicode__(self):
        return self.string

    class Meta:
#        unique_together = (('source_entity', 'string', 'language', 'tresource'),)
        verbose_name = _('translation string')
        verbose_name_plural = _('translation strings')
        ordering  = ['string',]
        order_with_respect_to = 'source_entity'
        get_latest_by = 'created'


#TODO: Consider and decide if we should merge it with Translation 
# (index field is the only one needed)
class PluralTranslation(models.Model):
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
    source_entity = models.ForeignKey(SourceEntity,
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
        unique_together = (('source_entity', 'string', 'language', 'index'),)
        verbose_name = _('plural translation string')
        verbose_name_plural = _('plural translation strings')
        ordering  = ['source_entity', 'index']
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
    Translation by using a heuristic.
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
    source_entity = models.ForeignKey(SourceEntity,
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
        # Only one suggestion can be committed by each user for a source_entity 
        # in a specific language!
        unique_together = (('source_entity', 'string', 'language'),)
        verbose_name = _('translation suggestion')
        verbose_name_plural = _('translation suggestions')
        ordering  = ['string',]
        order_with_respect_to = 'source_entity'
        get_latest_by = 'created'

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

    #resource = models.ForeignKey(TResource, verbose_name=_('TResource'),
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
        parser = None
        for p in PARSERS:
            if p.accept(self.name):
                parser = p
                break

        if not parser:
            return

        self.mime_type = parser.mime_type

        stringset = parser.parse_file(filename = self.get_storage_path()) 
        if not stringset:
            return

        if stringset.target_language:
            try:
                self.language = Language.objects.by_code_or_alias(stringset.target_language)
            except Language.DoesNotExist:
                pass

        self.total_strings = len(stringset.strings)
        return
