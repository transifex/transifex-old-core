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

# TODO More efficient plural fetching (we need HAVING num_rules > 1)
# TODO Or merge the queries


class TranslationsBuilder(object):
    """Builder to fetch the set of translations to use."""

    def __init__(self, resource, language):
        """Set the resource and language for the translation."""
        self.resource = resource
        self.language = language

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

    def plurals(self):
        """Get the pluralized translation strings.

        The returned translations are for the specified language.

        Returns:
            A dictionary with the translated strings. The keys are the id of
            the source entity this translation is for and the values are
            dictionaries themselves with keys being the rule number and
            values the translations for the specific (source_entity, rule).
        """
        raise NotImplementedError


class AllTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch all translations."""

    def __call__(self):
        """Get the translation strings that match the specified
        source_entities.
        """
        translations = Translation.objects.filter(
            resource=self.resource, language=self.language, rule=5
        ).values_list(
            'source_entity_id', 'string'
        ).iterator()
        return dict(translations)


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
        translations = Translation.objects.filter(reviewed=True,
            resource=self.resource, language=self.language, rule=5
        ).values_list('source_entity_id', 'string').iterator()
        return dict(translations)


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
        ).values_list(
            'source_entity_id', 'string'
        )
        source_entities = SourceEntity.objects.filter(
            resource=self.resource
        ).values_list('id', flat=True)
        missing_ids = set(source_entities) - set([sid for sid, s in translations])
        source_strings = Translation.objects.filter(
            source_entity__in=missing_ids,
            language=self.resource.source_language, rule=5
        ).values_list(
            'source_entity_id', 'string'
        )
        return dict(itertools.chain(translations, source_strings))


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
        ).values_list(
            'source_entity_id', 'string'
        )
        source_entities = SourceEntity.objects.filter(
            resource=self.resource
        ).values_list('id', flat=True)
        missing_ids = set(source_entities) - set([sid for sid, s in translations])
        source_strings = Translation.objects.filter(
            source_entity__in=missing_ids,
            language=self.resource.source_language, rule=5
        ).values_list(
            'source_entity_id', 'string'
        )
        return dict(itertools.chain(translations, source_strings))
