# -*- coding: utf-8 -*-
"""
String Level models.
"""

import datetime, sys, json
from hashlib import md5
from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User

from languages.models import Language
from projects.models import Project
from storage.models import StorageFile
from txcommon.db.models import CompressedTextField
from txcommon.log import logger

from resources import CACHE_KEYS as RESOURCES_CACHE_KEYS


# TODO: Parsers need to be somewhat rewritten, currently each one implements
# parse(buf) function which returns lib.core.StringSet class, and
# compile(stringset) which returns file buffer.
#
# It actually makes more sense to store all uploaded files, parse only the
# information we are interested in, and during compilation, take the uploaded
# file as template, and just replace modified parts


class ResourceManager(models.Manager):
    pass

class Resource(models.Model):
    """
    A translatable resource, such as a document, a set of strings etc.
    
    This is roughly equivalent to a POT file, string stream, or some other
    strings grouped together as a single translatable element.
    
    The resource is the rough equivalent to the deprecated 'Component' object,
    but with an important difference: a resource can only have one "source file"
    wheras the Component was able to encapsulate multiple ones.
    
    A resource is always related to a project.
    """

    name = models.CharField(_('Name'), max_length=255, null=False, blank=False,
        help_text=_("A descriptive name unique inside the project."))

    # Short identifier to be used in the API URLs
    slug = models.SlugField(_('Slug'), max_length=50,
        help_text=_("A short label to be used in the URL, containing only "
                    "letters, numbers, underscores or hyphens."))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # i18n related fields
    source_file = models.ForeignKey(StorageFile, verbose_name=_("Source file"),
        blank=True, null=True,
        help_text=_("A local file used to extract the strings to be "
                    "translated."))
    i18n_type = models.CharField(_('I18n type'), max_length=20,
        choices=((v,k) for k,v in settings.I18N_METHODS.items()),
        help_text=_("The type of i18n method used in this resource (%s)" %
                    ', '.join(settings.TRANS_CHOICES.keys())))
    # Foreign Keys
    source_language = models.ForeignKey(Language,
        verbose_name=_('Source Language'), blank=False, null=False,
        help_text=_("The source language of this Resource."))
    project = models.ForeignKey(Project, verbose_name=_('Project'),
        blank=False, null=True,
        help_text=_("The project the translation resource belongs to."))

    # Managers
    objects = ResourceManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.slug, self.project)

    def __repr__(self):
        return "<Resource: %s>" % self.slug

    class Meta:
        unique_together = ('slug', 'project',)
        verbose_name = _('resource')
        verbose_name_plural = _('resources')
        ordering  = ['name',]
        order_with_respect_to = 'project'
        get_latest_by = 'created'

    @models.permalink
    def get_absolute_url(self):
        return ('resource_detail', None,
            { 'project_slug': self.project.slug, 'resource_slug' : self.slug })

    @property
    def full_name(self):
        """
        Return a simple string without spaces identifying the resource.
        
        Can be used instead of __unicode__ to create files on disk, URLs etc.
        """        
        return "%s.%s" % (self.project.slug, self.slug)


    @property
    def source_strings(self):
        """Return the source language translations, including plurals."""
        return Translation.objects.filter(resource=self,
                                           language=self.source_language)

    @property
    def entities(self):
        """Return the resource's translation entities."""
        return SourceEntity.objects.filter(resource=self)


    @property
    def entities_count(self):
        """Return the number of source entities."""
        cache_key = (RESOURCES_CACHE_KEYS['source_strings_count'] % (self.project.slug, self.slug))
        sc = cache.get(cache_key)
        if not sc:
            sc = self.entities.count()
            cache.set(cache_key, sc)
        return sc


    @property
    def wordcount(self):
        """
        Return the number of words which need translation in this resource.
        
        The counting of the words uses the Translation objects of the SOURCE
        LANGUAGE as set of objects. This function does not count the plural 
        strings!
        """
        cache_key = (RESOURCES_CACHE_KEYS['word_count'] % (self.project.slug, self.slug))
        wc = cache.get(cache_key)
        if not wc:
            wc = 0
            for ss in self.source_strings:
                wc += ss.wordcount
            cache.set(cache_key, wc)
        return wc

    @property
    def last_committer(self):
        """
        Return the overall last committer for the translation of this resource.
        """
        lt = self.last_translation(language=None)
        if lt:
            return lt.user
        return None

    def last_translation(self, language=None):
        """
        Return the last translation for this Resource and the specific lang.
        
        If None language value then return in all languages avaible the last 
        translation.
        """
        if language:
            if not isinstance(language, Language):
                language = Language.objects.by_code_or_alias(language)
            t = Translation.objects.filter(resource=self,
                    language=language, rule=5).order_by('-last_update')
        else:
            t = Translation.objects.filter(resource=self,
                                           rule=5).order_by('-last_update')
        if t:
            return t[0]
        return None

    @property
    def available_languages(self):
        """
        Return the languages with at least one Translation of a SourceEntity for
        this Resource.
        """
        languages = Translation.objects.filter(resource=self).values_list(
            'language', flat=True).distinct()
        return Language.objects.filter(id__in=languages).distinct()

    def translated_strings(self, language):
        """
        Return the QuerySet of source entities, translated in this language.
        
        This assumes that we DO NOT SAVE empty strings for untranslated entities!
        """
        if not isinstance(language, Language):
            language = Language.objects.by_code_or_alias(language)

        return SourceEntity.objects.filter(resource=self,
            id__in=Translation.objects.filter(language=language,
                resource=self, rule=5).values_list('source_entity', flat=True))

    def untranslated_strings(self, language):
        """
        Return the QuerySet of source entities which are not yet translated in
        the specific language.
        
        This assumes that we DO NOT SAVE empty strings for untranslated entities!
        """
        if not isinstance(language, Language):
            language = Language.objects.by_code_or_alias(language)

        return SourceEntity.objects.filter(resource=self).exclude(
            id__in=Translation.objects.filter(language=language,
                resource=self, rule=5).values_list('source_entity', flat=True))

    def num_translated(self, language):
        """
        Return the number of translated strings in this Resource for the language.
        """
        return self.translated_strings(language).count()

    def num_untranslated(self, language):
        """
        Return the number of untranslated strings in this Resource for the language.
        """
        return self.untranslated_strings(language).count()

    def trans_percent(self, language):
        """Return the percent of untranslated strings in this Resource."""
        t = self.num_translated(language)
        try:
            return (t * 100 / self.entities_count)
        except ZeroDivisionError:
            return 100

    def untrans_percent(self, language):
        """Return the percent of untranslated strings in this Resource."""
        translated_percent = self.trans_percent(language)
        return (100 - translated_percent)
        # With the next approach we lose some data because we cut floating points
#        u = self.num_untranslated(language)
#        try:
#            return (u * 100 / self.entities_count)
#        except ZeroDivisionError:
#            return 0
    


    # XXX: Obsolete. Now that filehandlers are implemented the merge_*
    # methods are no longer needed.

    @transaction.commit_manually
    def merge_stringset(self, stringset, target_language, metadata=None, is_source=False, user=None, overwrite_translations=True):

        try:
            strings_added = 0
            strings_updated = 0
            for j in stringset.strings:
                # Check SE existence
                try:
                    se = SourceEntity.objects.get(
                        string = j.source_entity,
                        context = j.context or "None",
                        resource = self
                    )
                except SourceEntity.DoesNotExist:
                    # Skip creation of sourceentity object for non-source files.
                    if not is_source:
                        continue
                    # Create the new SE
                    se = SourceEntity.objects.create(
                        string = j.source_entity,
                        context = j.context or "None",
                        resource = self,
                        pluralized = j.pluralized,
                        position = 1,
                        # FIXME: this has been tested with pofiles only
                        occurrences = j.occurrences,
                    )

                # Skip storing empty strings as translations!
                if not se and not j.translation:
                    continue
                tr, created = Translation.objects.get_or_create(
                    source_entity = se,
                    language = target_language,
                    resource = self,
                    rule = j.rule,
                    defaults = {
                        'string' : j.translation,
                        'user' : user,
                        },
                    )

                if created and j.rule==5:
                    strings_added += 1

                if not created and overwrite_translations:
                    if tr.string != j.translation:
                        tr.string = j.translation
                        tr.save()
                        strings_updated += 1
        except Exception, e:
            logger.error("There was problem while importing the entries "
                         "into the database. Entity: '%s'. Error: '%s'."
                         % (j.source_entity, str(e)))
            transaction.rollback()
            return 0,0
        else:
            self.source_file_metadata = json.dumps(metadata)
            self.save()
            transaction.commit()
            return strings_added, strings_updated

class SourceEntity(models.Model):
    """
    A representation of a source string which is translated in many languages.
    
    The SourceEntity is pointing to a specific Resource and it is uniquely 
    defined by the string, context and resource fields (so they are unique
    together).
    """
    string = models.TextField(_('String'), blank=False, null=False,
        help_text=_("The actual string content of source string."))
    string_hash = models.CharField(_('String Hash'), blank=False, null=False,
        max_length=32, editable=False,
        help_text=_("The hash of the translation string used for indexing"))
    context = models.CharField(_('Context'), max_length=255,
        blank=False, null=False,
        help_text=_("A description of the source string. This field specifies"
                    "the context of the source string inside the resource."))
    position = models.IntegerField(_('Position'), blank=True, null=True,
        help_text=_("The position of the source string in the Resource."
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

    pluralized = models.BooleanField(_('Pluralized'), blank=False,
        null=False, default=False,
        help_text=_("Identify if the entity is pluralized ot not."))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    # A source string must always belong to a resource
    resource = models.ForeignKey(Resource, verbose_name=_('Resource'),
        blank=False, null=False, related_name='source_entities',
        help_text=_("The translation resource which owns the source string."))

    def __unicode__(self):
        return self.string

    class Meta:
        unique_together = (('string_hash', 'context', 'resource'),)
        verbose_name = _('source string')
        verbose_name_plural = _('source strings')
        ordering = ['string', 'context']
        order_with_respect_to = 'resource'
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        """
        Do some exra processing before the actual save to db.
        """
        # encoding happens to support unicode characters
        self.string_hash = md5(self.string.encode('utf-8')).hexdigest()
        super(SourceEntity, self).save(*args, **kwargs)

    def get_translation(self, lang_code, rule=5):
        """Return the current active translation for this entity."""
        try:
            return self.translations.get(language__code=lang_code, rule=rule)
        except Translation.DoesNotExist:
            return None


class TranslationManager(models.Manager):
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

    def by_string_and_language(self, string, source_code='en', target_code=None):
        """
        Search translation for source strings queries and only in Public projects!
        """
        query = models.Q()
        for term in string.split(' '):
            query &= models.Q(string__icontains=term)

        source_language = Language.objects.by_code_or_alias(source_code)

        # If no target language given search on any target language.
        if target_code:
            language = Language.objects.by_code_or_alias(target_code)
            results =  self.filter(language=language,
                source_entity__resource__project__in=Project.public.all(),
                source_entity__id__in=self.filter(query, language=source_language).values_list(
                    'source_entity', flat=True))
        else:
            results =  self.filter(
                source_entity__resource__project__in=Project.public.all(),
                source_entity__id__in=self.filter(query, language=source_language).values_list(
                    'source_entity', flat=True))
        return results

class Translation(models.Model):
    """
    The representation of a live translation for a given source string.
    
    This model encapsulates all the necessary fields for the translation of a 
    source string in a specific target language. It also contains a set of meta
    fields for the context of this translation.
    """

    string = models.TextField(_('String'), blank=False, null=False,
        help_text=_("The actual string content of translation."))
    string_hash = models.CharField(_('String Hash'), blank=False, null=False,
        max_length=32, editable=False,
        help_text=_("The hash of the translation string used for indexing"))
    rule = models.IntegerField(_('Plural rule'), blank=False,
        null=False, default=5,
        help_text=_("Number related to the plural rule of the translation. "
                    "It's 0=zero, 1=one, 2=two, 3=few, 4=many and 5=other. "
                    "For translations that have its entity not pluralized, "
                    "the rule must be 5 (other)."))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    # A source string must always belong to a resource
    source_entity = models.ForeignKey(SourceEntity,
        verbose_name=_('Source String'),
        related_name='translations',
        blank=False, null=False,
        help_text=_("The source string which is being translated by this"
                    "translation string instance."))

    language = models.ForeignKey(Language,
        verbose_name=_('Target Language'),blank=False, null=True,
        help_text=_("The language in which this translation string belongs to."))

    # Foreign Keys
    # A source string must always belong to a resource
    resource = models.ForeignKey(Resource, verbose_name=_('Resource'),
        blank=False, null=False,
        help_text=_("The translation resource which owns the source string."))

    user = models.ForeignKey(User,
        verbose_name=_('Committer'), blank=False, null=True,
        help_text=_("The user who committed the specific translation."))

    #TODO: Managers
    objects = TranslationManager()

    def __unicode__(self):
        return self.string

    class Meta:
        unique_together = (('source_entity', 'string_hash', 'language', 'resource',
            'rule'),)
        verbose_name = _('translation string')
        verbose_name_plural = _('translation strings')
        ordering  = ['string',]
        order_with_respect_to = 'source_entity'
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        """
        Do some exra processing before the actual save to db.
        """
        # encoding happens to support unicode characters
        self.string_hash = md5(self.string.encode('utf-8')).hexdigest()
        super(Translation, self).save(*args, **kwargs)

    @property
    def wordcount(self):
        """
        Return the number of words for this translation string.
        """
        # use None to split at any whitespace regardless of length
        # so for instance double space counts as one space
        return len(self.string.split(None))

class Template(models.Model):
    """
    Source file template for a specific resource.

    This model holds the source file template in a compressed textfield to save
    space in the database. All translation strings are changed with the md5
    hashes of the SourceEntity string which enables us to do a quick search and
    replace each time we want to recreate the file.
    """

    content = CompressedTextField(null=False, blank=False,
        help_text=_("This is the actual content of the template"))
    resource = models.ForeignKey(Resource,
        verbose_name="Resource",unique=True,
        blank=False, null=False,related_name="source_file_template",
        help_text=_("This is the template of the imported source file which is"
            " used to export translation files from the db to the user."))

    class Meta:
        verbose_name = _('Template')
        verbose_name_plural = _('Templates')
        ordering = ['resource']


# Signal registrations
from resources.handlers import *
models.signals.post_save.connect(on_save_invalidate_cache, sender=SourceEntity)
models.signals.post_delete.connect(on_delete_invalidate_cache, sender=SourceEntity)


from resources.formats.qt import LinguistHandler # Qt4 TS files
#from resources.formats.java import JavaPropertiesParser # Java .properties
#from resources.formats.apple import AppleStringsParser # Apple .strings
#from resources.formats.ruby import YamlParser # Ruby On Rails (broken)
#from resources.formats.resx import ResXmlParser # Microsoft .NET (not finished)
from resources.formats.pofile import POHandler # GNU Gettext .PO/.POT parser

PARSERS = [POHandler , LinguistHandler ] #, JavaPropertiesParser, AppleStringsParser]
