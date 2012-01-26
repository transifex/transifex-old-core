# -*- coding: utf-8 -*-

"""
Classes to build the set of translations to use for compilation.

These builders are responsible to fetch all translations to be
used, when compiling a template.
"""

import itertools
from transifex.resources.models import SourceEntity, Translation


class TranslationsBuilder(object):
    """Builder to fetch the set of translations to use."""

    def __init__(self, resource, language):
        """Set the resource and language for the translation."""
        self.resource = resource
        self.language = language

    def __call__(self, source_entities):
        """Get the translation strings that match the specified source_entities.

        The returned translations are for the specified langauge and rule = 5.

        Args:
            source_entities: A list of source entity ids.
        Returns:
            A dictionary with the translated strings. The keys are the id of
            the source entity this translation corresponds to and values are
            the translated strings.
        """
        # TODO Should return plurals
        raise NotImplementedError


class AllTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch all translations."""

    def __call__(self, resource):
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

    def __call__(self, resource):
        """Return an empty dictionary."""
        return {}


class ReviewedTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch only reviewed strings."""

    def __call__(self, resource):
        """Get the translation strings that match the specified source_entities
        and have been reviewed.
        """
        translations = Translation.objects.filter(reviewed=True,
            resource=self.resource, language=self.language, rule=5
        ).values_list('source_entity_id', 'string').iterator()
        return dict(translations)


class SourceTranslationsBuilder(TranslationsBuilder):
    """Builder to use source strings in case of missing strings."""

    def __call__(self, resource):
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
        source_entities = SourceEntity.objects.filter(resource=self.resource).values_list('id', flat=True)
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

    def __call__(self, resources):
        """Get the translation strings that match the specified
        source entities. Use the source strings for the missing
        ones.
        """
        # TODO Make caller use set
        source_entities = set(source_entities)
        translations = Translation.objects.filter(
            reviewed=True, resources=self.resource,
            language=self.language, rule=5
        ).values_list(
            'source_entity_id', 'string'
        )
        source_entities = SourceEntity.objects.filter(resource=self.resource).values_list('id', flat=True)
        missing_ids = set(source_entities) - set([sid for sid, s in translations])
        source_strings = Translation.objects.filter(
            source_entity__in=missing_ids,
            language=self.resource.source_language, rule=5
        ).values_list(
            'source_entity_id', 'string'
        )
        return dict(itertools.chain(translations, source_strings))
