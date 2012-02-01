# -*- coding: utf-8 -*-

"""
Classes to build the set of translations to use for compilation.

These builders are responsible to fetch all translations to be
used, when compiling a template.
"""

import itertools
import collections
from django.db.models import Count
from transifex.resources.models import SourceEntity, Translation


class TranslationsBuilder(object):
    """Builder to fetch the set of translations to use."""

    single_fields = ['source_entity_id', 'string']
    plural_fields = ['source_entity_id', 'string', 'rule']


    def __init__(self, resource, language):
        """Set the resource and language for the translation."""
        self.resource = resource
        self.language = language
        self.pluralized = False

    def __call__(self):
        """Get the translation strings that match the specified source_entities.

        The returned translations are for the specified language and rule = 5.

        Returns:
            A dictionary with the translated strings. The keys are the id of
            the source entity this translation corresponds to and values are
            the translated strings.
        """
        # TODO Should return plurals
        raise NotImplementedError

    def _single_output(self, iterable):
        """Output of builder for non-pluralized formats."""
        return dict(iterable)

    def _plurals_output(self, iterable):
        """Output of builder for pluralized formats."""
        res = collections.defaultdict(dict)
        for t in iterable:
            res[t[0]][t[2]] = t[1]
        return res

    def _set_pluralized(self, p):
        """Choose between pluralized and non-pluralized version."""
        if p:
            self._output = self._plurals_output
            self._fields = self.plural_fields
        else:
            self._output = self._single_output
            self._fields = self.single_fields
    pluralized = property(fset=_set_pluralized)


class AllTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch all translations."""

    def __call__(self):
        """Get the translation strings that match the specified
        source_entities.
        """
        translations = Translation.objects.filter(
            resource=self.resource, language=self.language
        ).values_list(*self._fields).iterator()
        return self._output(translations)


class EmptyTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch no translations."""

    def __init__(self, *args, **kwargs):
        super(EmptyTranslationsBuilder, self).__init__(None, None)

    def __call__(self):
        """Return an empty dictionary."""
        return {}


class ReviewedTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch only reviewed strings."""

    def __call__(self):
        """Get the translation strings that match the specified source_entities
        and have been reviewed.
        """
        translations = Translation.objects.filter(
            reviewed=True, resource=self.resource, language=self.language
        ).values_list(*self._fields).iterator()
        return self._output(translation)


class SourceTranslationsBuilder(TranslationsBuilder):
    """Builder to use source strings in case of missing strings."""

    def __call__(self):
        """Get the translation strings that match the specified
        source entities. Use the source strings for the missing
        ones.
        """
        # TODO Make caller use set
        translations = Translation.objects.filter(
            resource=self.resource, language=self.language, rule=5
        ).values_list(*self._fields)
        source_entities = SourceEntity.objects.filter(
            resource=self.resource
        ).values_list('id', flat=True)
        missing_ids = set(source_entities) - set([sid for sid, s in translations])
        source_strings = Translation.objects.filter(
            source_entity__in=missing_ids,
            language=self.resource.source_language, rule=5
        ).values_list(*self._fields)
        return self._output(itertools.chain(translations, source_strings))


class ReviewedSourceTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch only reviewed translations and fill the others
    with the source strings.
    """

    def __call__(self):
        """Get the translation strings that match the specified
        source entities. Use the source strings for the missing
        ones.
        """
        translations = Translation.objects.filter(
            reviewed=True, resources=self.resource,
            language=self.language, rule=5
        ).values_list(*self._fields)
        source_entities = SourceEntity.objects.filter(
            resource=self.resource
        ).values_list('id', flat=True)
        missing_ids = set(source_entities) - set([sid for sid, s in translations])
        source_strings = Translation.objects.filter(
            source_entity__in=missing_ids,
            language=self.resource.source_language, rule=5
        ).values_list(*self._fields)
        self._output(itertools.chain(translations, source_strings))
