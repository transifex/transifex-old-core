# -*- coding: utf-8 -*-

import copy
import json
import os
import codecs

from django.db import transaction
from django.db.models import get_model
from txcommon.log import logger
from happix.libtransifex.decorators import *
"""
STRICT flag is used to switch between two parsing modes:
  True - minor bugs in source files are treated fatal
    In case of Qt TS handler this means that buggy location elements will
    raise exceptions.
  False - if we get all necessary information from source files
    we will pass
"""
STRICT=False


Resource = get_model('happix', 'Resource')
Translation = get_model('happix', 'Translation')
SourceEntity = get_model('happix', 'SourceEntity')
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

class ParseError(StandardError):
    pass


class CompileError(StandardError):
    pass


class Handler(object):
    """
    Base class for writting file handlers for all the I18N types.
    """
    default_encoding = "utf-8"

    def __init__(self, filename=None, resource= None, language = None):
        """
        Initialize a File Handler either using a file or a Translation Queryset
        """

        self.filename = None # Input filename for associated translation file
        self.stringset = None # Stringset to extract entries from files
        self.metadata = None # Metadata of input file

        self.resource = None # Associated resource
        self.language = None # Resource's source language

        self.compiled = None # Var to store output of compile() method

        if filename:
            self.filename = filename
            #self.file = codecs.open(filename, "r", self.default_encoding )
        if resource:
            self.resource = resource
            self.language = resource.source_language
        if language:
            self.language = language



    def bind_file(self, filename):
        """
        Bind a file to an initialized POHandler.
        """
        if os.path.isfile(filename):
            self.filename = filename
        else:
            raise Exception("File does not exist")

    def bind_resource(self, resource):
        """
        Bind a resource to an initialized POHandler.
        """
        if isinstance(resource, Resource):
            self.resource = resource
            self.language = self.language or resource.source_language
            self.metadata = json.loads(resource.source_file_metadata or "{}")
        else:
            raise Exception("The specified object is not of the required type")


    @need_resource
    @need_language
    @need_stringset
    @transaction.commit_manually
    def save2db(self, is_source=False, user=None, overwrite_translations=True):
        """
        Saves parsed file contents to the database. duh
        """
        try:
            strings_added = 0
            strings_updated = 0
            for j in self.stringset.strings:
                # Check SE existence
                try:
                    se = SourceEntity.objects.get(
                        string = j.source_entity,
                        context = j.context or "None",
                        resource = self.resource
                    )
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

                # Skip storing empty strings as translations!
                if not se and not j.translation:
                    continue
                tr, created = Translation.objects.get_or_create(
                    source_entity = se,
                    language = self.language,
                    resource = self.resource,
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
            self.resource.source_file_metadata = json.dumps(self.metadata)
            self.resource.save()
            transaction.commit()
            return strings_added, strings_updated

    def accept(self, filename):
        return False

    def parse(self, buf):
        raise Exception("Handler.parse(buf) has to be overridden")

    def parse_file(self, filename, is_source=False, lang_rules=None):
        fh = open(filename, "ru")
        return self.parse(fh.read(), is_source, lang_rules)


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
    Store translations of any kind of I18N type (POT, QT, etc...).

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
