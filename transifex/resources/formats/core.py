# -*- coding: utf-8 -*-

import codecs, copy, os, re
from django.utils import simplejson as json

from django.conf import settings
from django.db import transaction
from django.db.models import get_model
from transifex.txcommon.log import logger
from transifex.languages.models import Language
from suggestions.models import Suggestion
from suggestions.formats import ContentSuggestionFormat
from transifex.actionlog.models import action_logging
from transifex.resources.handlers import invalidate_stats_cache
from transifex.resources.formats import FormatError
from transifex.resources.formats.pseudo import PseudoTypeMixin
from transifex.resources.formats.utils.decorators import *
from transifex.resources.signals import post_save_translation

# Temporary
from transifex.txcommon import notifications as txnotification
# Addons
from watches.models import TranslationWatch

"""
STRICT flag is used to switch between two parsing modes:
  True - minor bugs in source files are treated fatal
    In case of Qt TS handler this means that buggy location elements will
    raise exceptions.
  False - if we get all necessary information from source files
    we will pass
"""
STRICT=False


Resource = get_model('resources', 'Resource')
Translation = get_model('resources', 'Translation')
SourceEntity = get_model('resources', 'SourceEntity')
Template = get_model('resources', 'Template')
Storage = get_model('storage', 'StorageFile')

class CustomSerializer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, GenericTranslation):
            d = {
                'source_entity' : obj.source_entity,
                'translation' : obj.translation,
            }
            if obj.occurrences:
                d['occurrences'] = obj.occurrences
            if obj.comments:
                d['comments'] = obj.comments
            if obj.context:
                d['context'] = obj.context
            if obj.rule:
                d['rule'] = obj.rule
            if obj.pluralized:
                d['pluralized'] = obj.pluralized

            return d

        if isinstance(obj, StringSet):
            return {
                #'filename' : obj.filename,
                'target_language' : obj.target_language,
                'strings' : obj.strings,
            }

class ParseError(FormatError):
    """Base class for parsing errors."""
    pass


class CompileError(FormatError):
    """Base class for all compiling errors."""
    pass


class Handler(object):
    """
    Base class for writing file handlers for all the I18N types.
    """
    default_encoding = "UTF-8"
    method_name = None
    format_encoding = "UTF-8"

    HandlerParseError = ParseError
    HandlerCompileError = CompileError

    SuggestionFormat = ContentSuggestionFormat

    @classmethod
    def accepts(cls, i18n_type):
        """Accept only files that have the correct type specified."""
        return i18n_type == cls.method_name

    def __init__(self, filename=None, resource=None, language=None, content=None):
        """
        Initialize a formats handler.
        """
        self.filename = filename # Input filename for associated translation file
        self.content = self._get_content(filename=filename, content=content) # The content of the translation file
        self.stringset = None # Stringset to extract entries from files

        self.resource = None # Associated resource
        self.language = None # Resource's source language

        self.template = None # Var to store raw template
        self.compiled_template = None # Var to store output of compile() method

        if resource:
            self.resource = resource
            self.language = resource.source_language
        if language:
            self.language = language

    def _check_content(self, content):
        """
        Perform the actual check of the content.

        A subclass needs to only override this method to customize the check.
        """
        # FIXME Make all code use return values instead of exceptions
        # FIXME Needs to deprecate API v1
        return (True, None)

    def is_content_valid(self, content=None):
        """
        Check whether the content is valid for the format.

        Delegate the check to _check_content().
        """
        if content is None:
            content = self.content
            assert content is not None
        return self._check_content(content)

    ####################
    # Helper functions #
    ####################

    def _get_content(self, filename=None, content=None):
        """Read the content of the specified file."""
        if content is not None:
            return content
        if filename is None:
            return None
        f = codecs.open(filename, 'r', encoding=self.format_encoding)
        try:
            return f.read()
        except IOError, e:
            logger.warning(
                "Error opening file %s with encoding %s: %s" %\
                    (filename, self.format_encoding, e.message),
                exc_info=True
            )
            raise FormatError(e.message)
        except Exception, e:
            logger.warning("Unhandled exception: %s" % e.message, exc_info=True)
        finally:
            f.close()

    def set_language(self, language):
        """
        Set the language for the handler.
        """
        if isinstance(language, Language):
            self.language = language
        else:
            try:
                self.language = Language.objects.by_code_or_alias(language)
            except Language.DoesNotExist, e:
                logger.warning("Language.DoesNotExist: %s" % e.message, exc_info=True)
                raise FormatError(e.message)
            except Exception, e:
                logger.error(e.message, exc_info=True)
                raise FormatError(e.message)

    def bind_content(self, content):
        """
        Bind some content to the handler.
        """
        self.content = self._get_content(content)

    def bind_file(self, filename):
        """
        Bind a file to an initialized POHandler.
        """
        if os.path.isfile(filename):
            self.filename = filename
            self.content = self._get_content(filename=filename)
        else:
            msg = "Specified file %s does not exist." % filename
            logger.error(msg)
            raise FormatError(msg)

    def bind_resource(self, resource):
        """
        Bind a resource to an initialized POHandler.
        """
        if isinstance(resource, Resource):
            self.resource = resource
            try:
                resource_template = self.resource.source_file_template
            except Template.DoesNotExist:
                resource_template = None
            self.compiled_template = self.compiled_template or resource_template
            self.language = self.language or resource.source_language
        else:
            msg = "The specified object %s is not of type Resource" % resource
            logger.error(msg)
            raise FormatsError(msg)


    def bind_pseudo_type(self, pseudo_type):
        if isinstance(pseudo_type, PseudoTypeMixin):
            self.pseudo_type = pseudo_type
        else:
            raise Exception("pseudo_type needs to be based on type %s" %
                PseudoTypeMixin.__class__)


    def find_linesep(self, file_):
        """Find the line separator used in the file."""
        line = file_.readline()
        if line.endswith("\r\n"):  # windows line ending
            self._linesep = "\r\n"
        elif line.endswith("\r"):  # macosx line ending
            self._linesep = "\r"
        else:
            self._linesep = "\n"
        file_.seek(0)

    def _prepare_line(self, line):
        """
        Prepare a line for parsing.

        Remove newline and whitespace characters.
        """
        return line.rstrip('\r\n').strip()

    ####################
    #  Core functions  #
    ####################

    def _pseudo_decorate(self, string):
        """
        Modify the string accordingly to a ``pseudo_type`` set to the handler.
        This is used to export Pseudo Localized files.
        """
        if hasattr(self,'pseudo_type') and self.pseudo_type:
            nonunicode = False
            if isinstance(string, str):
                string = string.decode(self.default_encoding)
                nonunicode = True

            string = self.pseudo_type.compile(string)

            if nonunicode:
                string = string.encode(self.default_encoding)
        return string

    def _replace_translation(self, original, replacement, text):
        """
        Do a search and replace inside `text` and replaces all
        occurrences of `original` with `replacement`.
        """
        return re.sub(re.escape(original),
            self._pseudo_decorate(self._escape(replacement)), text)

    def _get_strings(self, resource):
        return SourceEntity.objects.filter(
            resource=resource
        )

    def _get_translation(self, string, language, rule):
        try:
            return Translation.objects.get(
                resource = self.resource, source_entity=string,
                language=language, rule=rule
            )
        except Translation.DoesNotExist, e:
            return None

    def _pre_compile(self, *args, **kwargs):
        """
        This is called before doing any actual work. Override in inherited
        classes to alter behaviour.
        """
        pass

    def _escape(self, s):
        """
        Escape special characters in string.
        """
        return s

    def _add_translation_string(self, *args, **kwargs):
        """Adds to instance a new translation string."""
        self.stringset.strings.append(GenericTranslation(*args, **kwargs))

    def _add_suggestion_string(self, *args, **kwargs):
        """Adds to instance a new suggestion string."""
        self.suggestions.strings.append(GenericTranslation(*args, **kwargs))

    def _apply_translation(self, source, trans, content):
        """Apply a translation to text.

        Usually, we do a search for the hash code of source and replace
        with trans.

        Args:
            source: The source entity.
            trans: The translation object.
            content: The text for the search-&-replace.

        Returns:
            The content after the translation has been applied.
        """
        return self._replace_translation(
            "%s_tr" % source.string_hash.encode(self.default_encoding),
            trans and trans.string.encode(self.default_encoding) or "",
            content
        )

    def _examine_content(self, content):
        """
        Offer a chance to peek into the template before any string is
        compiled.
        """
        return content

    def _post_compile(self, *args, **kwargs):
        """
        This is called in the end of the compile method. Override if you need
        the behaviour changed.
        """
        pass

    @need_resource
    def compile(self, language=None):
        """
        Compile the template using the database strings. The result is the
        content of the translation file.

        There are three hooks a subclass can call:
          _pre_compile: This is called first, before anything takes place.
          _examine_content: This is called, to have a look at the content/make
              any adjustments before it is used.
          _post_compile: Called at the end of the process.

        Args:
          language: The language of the file
        """

        if language is None:
            language = self.language
        self._pre_compile(language)
        content = Template.objects.get(resource=self.resource).content
        content = self._examine_content(content)
        try:
            self.compiled_template = self._compile(content, language)
        except Exception, e:
            logger.error("Error compiling file: %s" % e, exc_info=True)
            raise
        self._post_compile(language)

    def _compile(self, content, language):
        """Internal compile function.

        Subclasses must override this method, if they need to change
        the compile behavior.

        Args:
            content: The content (template) of the resource.
            language: The language for the translation.

        Returns:
            The compiled template.
        """
        stringset = self._get_strings(self.resource)
        for string in stringset:
            trans = self._get_translation(string, language, 5)
            content = self._apply_translation(string, trans, content)
        return content

    #######################
    #  save methods
    #######################

    def _context_value(self, context):
        """Convert the context for the database.

        Args:
            context: The context value calculated
        Returns:
            The correct value for the context ot be used in the database.
        """
        return context or u'None'

    def _handle_update_of_resource(self, user):
        """Do extra stuff after a source language/translation has been updated.

        Args:
            user: The user that caused the update.
        """
        self._update_stats_of_resource(self.resource, self.language, user)

        if self.language == self.resource.source_language:
            nt = 'project_resource_changed'
        else:
            nt = 'project_resource_translated'
        context = {
            'project': self.resource.project,
            'resource': self.resource,
            'language': self.language
        }
        object_list = [self.resource.project, self.resource, self.language]

        # if we got no user, skip the log
        if user:
            action_logging(user, object_list, nt, context=context)

        if settings.ENABLE_NOTICES:
            self._send_notices(signal=nt, extra_context=context)

    def _pre_save2db(self, *args, **kwargs):
        """
        This is called before doing any actual work. Override in inherited
        classes to alter behaviour.
        """
        pass

    def _post_save2db(self, strings_added, strings_updated, strings_deleted,
            is_source, user, overwrite_translations, **kwargs):
        """
        This is called in the end of the save2db method. Override if you need
        the behaviour changed.
        """
        kwargs.update({
            'strings_added': strings_added,
            'strings_updated': strings_updated,
            'strings_deleted': strings_deleted,
            'is_source': is_source,
            'user': user,
            'overwrite_translations': overwrite_translations,
            'resource': self.resource,
            'language': self.language
            })
        post_save_translation.send(sender=self, **kwargs)

    def _send_notices(self, signal, extra_context):
        txnotification.send_observation_notices_for(
            self.resource.project, signal, extra_context
        )

        # if language is source language, notify all languages for the change
        if self.language == self.resource.source_language:
            for l in self.resource.available_languages:
                twatch = TranslationWatch.objects.get_or_create(
                    resource=self.resource, language=l)[0]
                logger.debug(
                    "addon-watches: Sending notification for '%s'" % twatch
                )
                txnotification.send_observation_notices_for(
                    twatch,
                    signal='project_resource_translation_changed',
                    extra_context=extra_context
                )

    def _should_skip_translation(self, se, trans):
        """Check if current translation should be skipped, ie not saved to db.

        This should happen for empty translations (ie, untranslated strings)
        and for strings which are not correctly pluralized.

        Args:
            se: The source entity that corresponds to the translation.
            trans: The translation itself.
        Returns:
            True, if the specified translation must be skipped, ie not
            saved to database.
        """
        return not trans.translation or trans.pluralized != se.pluralized

    def _save_source(self, user, overwrite_translations):
        """Save source language translations to the database.

        Subclasses should override this method, if they need to customize
        the behavior of saving translations in the source language.

        Any fatal exception must be reraised.

        Args:
            user: The user that made the commit.
            overwrite_translations: A flag to indicate whether translations
                should be overrided.

        Returns:
            A tuple of number of strings added, updted and deleted.

        Raises:
            Any exception.
        """
        qs = SourceEntity.objects.filter(resource=self.resource)
        original_sources = list(qs) # TODO Use set() instead? Hash by pk
        new_entities = []
        source_entities = SourceEntityCollection()
        for se in original_sources:
            source_entities.add(se)

        qs = Translation.objects.filter(
            language=self.language, source_entity__in=source_entities.se_ids
        ).iterator()
        translations = TranslationCollection()
        for t in qs:
            translations.add(t)

        strings_added = 0
        strings_updated = 0
        strings_deleted = 0
        try:
            for j in self.stringset.strings:
                if j in source_entities:
                    se = source_entities.get(j)
                    # update source string attributes.
                    se.flags = j.flags or ""
                    se.pluralized = j.pluralized
                    se.developer_comment = j.comment or ""
                    se.occurrences = j.occurrences
                    se.save()
                    try:
                        original_sources.remove(se)
                    except ValueError:
                        # When we have plurals, we can't delete the se
                        # everytime, so we just pass
                        pass
                else:
                    # Create the new SE
                    se = SourceEntity.objects.create(
                        string = j.source_entity,
                        context = self._context_value(j.context),
                        resource = self.resource, pluralized = j.pluralized,
                        position = 1,
                        # FIXME: this has been tested with pofiles only
                        flags = j.flags or "",
                        developer_comment = j.comment or "",
                        occurrences = j.occurrences,
                    )
                    # Add it to list with new entities
                    new_entities.append(se)
                    source_entities.add(se)

                if self._should_skip_translation(se, j):
                    continue
                if (se, j) in translations:
                    if overwrite_translations:
                        tr = translations.get((se, j))
                        if tr.string != j.translation:
                            tr.string = j.translation
                            tr.user = user
                            tr.save()
                            strings_updated += 1
                else:
                    tr = Translation.objects.create(
                        source_entity=se, language=self.language, rule=j.rule,
                        string=j.translation, user=user, resource = self.resource
                    )
                    translations.add(tr)
                    if j.rule==5:
                        strings_added += 1
        except Exception, e:
            logger.error(
                "There was a problem while importing the entries into the "
                "database. Entity: '%s'. Error: '%s'." % (
                    j.source_entity, e.message
                )
            )
            raise

        sg_handler = self.SuggestionFormat(self.resource, self.language, user)
        sg_handler.add_from_strings(self.suggestions.strings)
        sg_handler.create_suggestions(original_sources, new_entities)
        self._update_template(self.template)

        strings_deleted = len(original_sources)
        return strings_added, strings_updated, strings_deleted

    def _save_translation(self, user, overwrite_translations):
        """Save other language translations to the database.

        Subclasses should override this method, if they need to customize
        the behavior of saving translations in other languages than the source
        one.

        Any fatal exception must be reraised.

        Args:
            user: The user that made the commit.
            overwrite_translations: A flag to indicate whether translations
                should be overrided.

        Returns:
            A tuple of number of strings added, updted and deleted.

        Raises:
            Any exception.
        """
        qs = SourceEntity.objects.filter(resource=self.resource).iterator()
        source_entities = SourceEntityCollection()
        for se in qs:
            source_entities.add(se)

        qs = Translation.objects.filter(
            language=self.language, source_entity__in=source_entities.se_ids
        ).iterator()
        translations = TranslationCollection()
        for t in qs:
            translations.add(t)

        strings_added = 0
        strings_updated = 0
        strings_deleted = 0
        try:
            for j in self.stringset.strings:
                if j not in source_entities:
                    continue
                else:
                    se = source_entities.get(j)

                if self._should_skip_translation(se, j):
                    continue
                if (se, j) in translations:
                    tr = translations.get(se, j)
                    if overwrite_translations:
                        if tr.string != j.translation:
                            tr.string = j.translation
                            tr.user = user
                            tr.save()
                            strings_updated += 1
                else:
                    tr = Translation.objects.create(
                        source_entity=se, language=self.language, rule=j.rule,
                        string=j.translation, user=user, resource=self.resource
                    )
                    if j.rule==5:
                        strings_added += 1
        except Exception, e:
            logger.error(
                "There was a problem while importing the entries into the "
                "database. Entity: '%s'. Error: '%s'." % (
                    j.source_entity, e.message
                )
            )
            raise
        sg_handler = ContentSuggestionFormat(self.resource, self.language, user)
        sg_handler.add_from_strings(self.suggestions.strings)
        return strings_added, strings_updated, strings_deleted

    def _update_stats_of_resource(self, resource, language, user):
        """Update the statistics for the resource.

        Also, invalidate any caches.
        """
        invalidate_stats_cache(resource, language, user=user)

    def _update_template(self, content):
        """Update the template of the resource.

        Args:
            content: The content of the template.
        """
        t, created = Template.objects.get_or_create(resource=self.resource)
        t.content = content
        t.save()

    @need_resource
    @need_language
    @need_stringset
    @transaction.commit_manually
    def save2db(self, is_source=False, user=None, overwrite_translations=True):
        """
        Saves parsed file contents to the database. duh
        """
        self._pre_save2db(is_source, user, overwrite_translations)
        try:
            if is_source:
                (added, updated, deleted) = self._save_source(
                    user, overwrite_translations
                )
            else:
                (added, updated, deleted) = self._save_translation(
                    user, overwrite_translations
                )
        except Exception, e:
            logger.warning(
                "Failed to save translations for language %s and resource %s."
                "Error was %s." % (self.language, self.resource, e.message),
                exc_info=True
            )
            transaction.rollback()
            return (0, 0)
        self._post_save2db(is_source , user, overwrite_translations)
        if added + updated + deleted > 0:
            self._handle_update_of_resource(user)
        transaction.commit()
        return (added, updated)

    ####################
    # parse methods
    ####################

    def _generate_template(self, obj):
        """Generate a template from the specified object.

        By default, we use the obj as a unicode string and encode it to
        str.

        Subclasses could override this.
        """
        return obj.encode(self.default_encoding)

    def _parse(self, is_source, lang_rules):
        """The actual functions that parses the content.

        Formats need to override this to provide the desired behavior.

        Two stringsets are available to subclasses:
        - self.stringset to save the translated strings
        - self.suggestions to save suggested translations

        Args:
            is_source: Flag to determine if this is a source file or not.
            lang_rules: rules for the language

        Returns:
            An object which, when used as an argument in
            `self._create_template()`, the template for the resource
            is generated.

        """
        raise NotImplementedError

    @need_content
    @need_language
    def parse_file(self, is_source=False, lang_rules=None):
        """Parse the content."""
        self.stringset = StringSet()
        self.suggestions = StringSet()
        obj = self._parse(is_source, lang_rules)
        if is_source:
            self.template = self._generate_template(obj)


class StringSet(object):
    """
    Store a list of Translation objects for a given language.
    """
    def __init__(self):
        self.strings = []
        self.target_language = None

    def strings_grouped_by_context(self):
        d = {}
        for i in self.strings:
            if i.context in d:
                d[i.context].append(i)
            else:
                d[i.context] = [i,]
        return d

    def to_json(self):
        return json.dumps(self, cls=CustomSerializer)


class GenericTranslation(object):
    """
    Store translations of any kind of I18N type (POT, Qt, etc...).

    Parameters:
        source_entity - The original entity found in the source code.
        translation - The related source_entity written in another language.
        context - The related context for the source_entity.
        occurrences - Occurrences of the source_entity from the source code.
        comments - Comments for the given source_entity from the source code.
        rule - Plural rule 0=zero, 1=one, 2=two, 3=few, 4=many or 5=other.
        pluralized - True if the source_entity is a plural entry.
        fuzzy - True if the translation is fuzzy/unfinished
        obsolete - True if the entity is obsolete
    """
    def __init__(self, source_entity, translation, occurrences=None,
            comment=None, flags=None, context=None, rule=5, pluralized=False,
            fuzzy=False, obsolete=False):
        self.source_entity = source_entity
        self.translation = translation
        self.context = context
        self.occurrences = occurrences
        self.comment = comment
        self.flags = flags
        self.rule = int(rule)
        self.pluralized = pluralized
        self.fuzzy = fuzzy
        self.obsolete = obsolete

    def __hash__(self):
        if STRICT:
            return hash((self.source_entity, self.translation,
                self.occurrences))
        else:
            return hash((self.source_entity, self.translation))

    def __eq__(self, other):
        if isinstance(other, self.__class__) and \
            self.source_entity == other.source_entity and \
            self.translation == other.translation and \
            self.context == other.context:
            return True
        return False


class ResourceItems(object):
    """base class for collections for resource items (source entities,
    translations, etc).
    """

    def __init__(self):
        self._items = {}

    def get(self, item):
        """Get a source entity in the collection or None."""
        key = self._generate_key(item)
        return self._items.get(key, None)

    def add(self, item):
        """Add a source entity to the collection."""
        key = self._generate_key(item)
        self._items[key] = item

    def __contains__(self, item):
        key = self._generate_key(item)
        return key in self._items

    def __iter__(self):
        return iter(self._items)


class SourceEntityCollection(ResourceItems):
    """A collection of source entities."""

    def _generate_key(self, se):
        """Generate a key for this se, which is guaranteed to
        be unique within a resource.
        """
        if isinstance(se, GenericTranslation):
            return self._create_unique_key(se.source_entity, se.context)
        elif isinstance(se, SourceEntity):
            return self._create_unique_key(se.string, se.context)

    def _create_unique_key(self, source_string, context):
        """Create a unique key based on the source_string and the context.

        Args:
            source_string: The source string.
            context: The context.
        Returns:
            A tuple to be used as key.
        """
        if not context:
            return (source_string, u'None')
        elif isinstance(context, list):
            return (source_string, u':'.join(x for x in context))
        else:
            return (source_string, context)

    def se_ids(self):
        """Return the ids of the sourc entities."""
        return set(map(lambda se: se.id, self._items.itervalues()))


class TranslationCollection(ResourceItems):
    """A collection of translations."""

    def _generate_key(self, t):
        """Generate a key for this se, which is guaranteed to
        be unique within a resource.

        Args:
            t: a translation (sort of) object.
            se_id: The id of the source entity of this translation.
        """
        if isinstance(t, Translation):
            return self._create_unique_key(t.source_entity_id, t.rule)
        elif isinstance(t, tuple):
            return self._create_unique_key(t[0].id, t[1].rule)
        else:
            return None

    def _create_unique_key(self, se_id, rule):
        """Create a unique key based on the source_string and the context.

        Args:
            se_id: The id of the source string this translation corresponds to.
            rule: The rule of the language this translation is for.
        Returns:
            A tuple to be used as key.
        """
        assert se_id is not None
        return (se_id, rule)

    def se_ids(self):
        """Get the ids of the source entities in the collection."""
        return set(map(lambda t: t[0], self._items.iterkeys()))
