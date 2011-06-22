# -*- coding: utf-8 -*-

import codecs, copy, os, re
from django.utils import simplejson as json

from django.conf import settings
from django.db import transaction
from django.db.models import get_model
from transifex.txcommon.log import logger
from transifex.languages.models import Language
from suggestions.models import Suggestion
from transifex.actionlog.models import action_logging
from transifex.resources.handlers import invalidate_stats_cache
from transifex.resources.formats import FormatError
from transifex.resources.formats.pseudo import PseudoTypeMixin
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.string_utils import percent_diff
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
        except Exception, e:
            logger.warning(
                "Error opening file %s with encoding %s" % (filename, self.format_encoding),
                exc_info=True
            )
            raise FormatError(e.message)
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

    @need_resource
    @need_language
    @need_stringset
    @transaction.commit_manually
    def save2db(self, is_source=False, user=None, overwrite_translations=True):
        """
        Saves parsed file contents to the database. duh
        """
        self._pre_save2db(is_source, user, overwrite_translations)

        if is_source:
            qs = SourceEntity.objects.filter(resource=self.resource)
            original_sources = list(qs)
            new_entities = []

        try:
            strings_added = 0
            strings_updated = 0
            strings_deleted = 0
            for j in self.stringset.strings:
                # Check SE existence
                try:
                    se = SourceEntity.objects.get(
                        string = j.source_entity,
                        context = j.context or "None",
                        resource = self.resource
                    )
                    if is_source:
                        # If it's a source file, we need to update source
                        # string attributes.
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
                except SourceEntity.DoesNotExist:
                    # Skip creation of sourceentity object for non-source files.
                    if not is_source:
                        continue
                    # Create the new SE
                    se = SourceEntity.objects.create(
                        string = j.source_entity,
                        context = j.context or "None",
                        resource = self.resource,
                        pluralized = j.pluralized,
                        position = 1,
                        # FIXME: this has been tested with pofiles only
                        flags = j.flags or "",
                        developer_comment = j.comment or "",
                        occurrences = j.occurrences,
                    )
                    # Add it to list with new entities
                    new_entities.append(se)

                # Skip storing empty strings as translations and don't save not
                # pluralized entries in pluralized source entities
                if not j.translation or j.pluralized != se.pluralized:
                    continue

                tr, created = Translation.objects.get_or_create(
                    source_entity = se,
                    language = self.language,
                    rule = j.rule,
                    defaults = {
                        'string' : j.translation,
                        'user' : user,
                        },
                    resource = self.resource
                    )

                if created and j.rule==5:
                    strings_added += 1

                if not created and overwrite_translations:
                    if tr.string != j.translation:
                        tr.string = j.translation
                        tr.user = user
                        tr.save()
                        strings_updated += 1
        except Exception, e:
            logger.error("There was problem while importing the entries "
                         "into the database. Entity: '%s'. Error: '%s'."
                         % (j.source_entity, str(e)))
            transaction.rollback()
            return 0,0
        else:
            if is_source:
                strings_deleted = len(original_sources)
                t, created = Template.objects.get_or_create(resource = self.resource)
                t.content = self.template
                t.save()
                if created:
                    self.resource.i18n_type = get_i18n_type_from_file(self.filename)
                    self.resource.save()
                # See how many iterations we need for this
                iterations = len(original_sources)*len(new_entities)
                # If it's not over the limit, then do it
                if iterations < settings.MAX_STRING_ITERATIONS:
                    for se in original_sources:
                        for ne in new_entities:
                            try:
                                old_trans = Translation.objects.get(source_entity=se,
                                    language=se.resource.source_language, rule=5)
                                new_trans = Translation.objects.get(source_entity=ne,
                                    language=se.resource.source_language, rule=5)
                            except Translation.DoesNotExist:
                                # Source language translation should always exist
                                # but just in case...
                                continue
                            # find Levenshtein distance
                            if percent_diff(old_trans.string, new_trans.string) < settings.MAX_STRING_DISTANCE:
                                convert_to_suggestions(se, ne, user)
                                break

                        se.delete()
                else:
                    for se in original_sources:
                        se.delete()

            for j in self.suggestions.strings:
                # Check SE existence
                try:
                    se = SourceEntity.objects.get(
                        string = j.source_entity,
                        context = j.context or "None",
                        resource = self.resource
                    )
                except SourceEntity.DoesNotExist:
                    continue

                tr, created = Suggestion.objects.get_or_create(
                    string = j.translation,
                    source_entity = se,
                    language = self.language
                )

            self._post_save2db(strings_added, strings_updated, strings_deleted,
                is_source, user, overwrite_translations)

            if strings_added + strings_updated + strings_deleted > 0:
                # Invalidate cache after saving file
                invalidate_stats_cache(self.resource, self.language, user=user)

                if self.language == self.resource.source_language:
                    nt = 'project_resource_changed'
                else:
                    nt = 'project_resource_translated'
                context = {'project': self.resource.project,
                            'resource': self.resource,
                            'language': self.language}
                object_list = [self.resource.project, self.resource, self.language]
                # if we got no user, skip the log
                if user:
                    action_logging(user, object_list, nt, context=context)

                if settings.ENABLE_NOTICES:
                    txnotification.send_observation_notices_for(self.resource.project,
                            signal=nt, extra_context=context)

                    # if language is source language, notify all languages for the change
                    if self.language == self.resource.source_language:
                        for l in self.resource.available_languages:
                            twatch = TranslationWatch.objects.get_or_create(
                                resource=self.resource, language=l)[0]
                            logger.debug("addon-watches: Sending notification"
                                " for '%s'" % twatch)
                            txnotification.send_observation_notices_for(twatch,
                            signal='project_resource_translation_changed',
                                 extra_context=context)

            transaction.commit()
            return strings_added, strings_updated

    def _parse(self, is_source, lang_rules):
        raise NotImplementedError

    @need_content
    @need_language
    def parse_file(self, is_source=False, lang_rules=None):
        """Parse the content."""
        self._parse(is_source, lang_rules)


def convert_to_suggestions(source, dest, user=None, langs=None):
    """
    This function takes all translations that belong to source and adds them as
    suggestion to dest. Both source and dest are SourceEntity objects.

    The langs can contain a list of all languages for which the conversion will
    take place. Defaults to all available languages.
    """
    if langs:
        translations = Translation.objects.filter(source_entity=source,
            language__in=langs, rule=5)
    else:
        translations = Translation.objects.filter(source_entity=source, rule=5)

    for t in translations:
        # Skip source language translations
        if t.language == dest.resource.source_language:
            continue

        tr, created = Suggestion.objects.get_or_create(
            string = t.string,
            source_entity = dest,
            language = t.language
        )

        # If the suggestion was created and we have a user assign him as the
        # one who made the suggestion
        if created and user:
            tr.user = user
            tr.save()

    return

class StringSet:
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


class GenericTranslation:
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
