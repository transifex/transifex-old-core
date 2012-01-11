# -*- coding: utf-8 -*-

"""
Compilation related objects.
"""

import re
from transifex.txcommon.log import logger
from transifex.resources.models import SourceEntity, Translation
from transifex.resources.formats.exceptions import UninitializedCompilerError


class Compiler(object):
    """Class to compile translation files.

    There is a set of translation strings obtained from
    the database, while the template is given by the caller.

    We use extra builders for the steps of fetching the set of
    translations (``translations``) for the language and for the
    type of translation we want (``tdecorator). This allows for
    full customization of those steps. See
    http://en.wikipedia.org/wiki/Builder_pattern.
    """

    def __init__(self, resource, **kwargs):
        """Set the variables of the object.

        The object is not fully initialized, unless the two
        builders have been set.

        Allows subclasses to add extra keyword arguments.

        Args:
            resource: The resource which the compilation is for.
        """
        self.resource = resource
        for arg, value in kwargs.items():
            setattr(self, arg, value)
        self._initialized = False
        self._translations = None
        self._tdecorator = None

    def _set_tset(self, t):
        self._tset = t
    translation_set = property(fset=_set_tset)

    def _set_tdecorator(self, a):
        self._tdecorator = a
    translation_decorator = property(fset=_set_tdecorator)

    def compile(self, template, language):
        """Compile the template using the database strings.

        The result is the content of the translation file.

        There are three hooks a subclass can call:
          _pre_compile: This is called first, before anything takes place.
          _examine_content: This is called, to have a look at the content/make
              any adjustments before it is used.
          _post_compile: Called at the end of the process.

        Args:
            template: The template to compile. It must be a unicode string.
            language: The language of the translation.
        Returns:
            The compiled template as a unicode string.
        """
        self.language = language
        if self._tset is None or self._tdecorator is None:
            msg = "One of the builders has not been set."
            raise UninitializedCompilerError(msg)
        self._pre_compile()
        content = self._examine_content(template)
        self._compile(content)
        self._post_compile()
        del self.language
        return self.compiled_template

    def _apply_translation(self, source_hash, trans, content):
        """Apply a translation to the content.

        Usually, we do a search for the hash code of source and replace
        with trans.

        Args:
            source_hash: The hash string of the source entity.
            trans: The translation string.
            content: The text for the search-&-replace.
        Returns:
            The content after the translation has been applied.
        """
        return self._replace_translation(
            "%s_tr" % source_hash, self._tdecorator(trans), content
        )

    def _compile(self, content):
        """Internal compile function.

        Subclasses must override this method, if they need to change
        the compile behavior.

        Args:
            content: The content (template) of the resource.
        """
        stringset = self._get_source_strings()
        translations = self._tset(s[0] for s in stringset)
        for string in stringset:
            trans = translations.get(string[0], u"")
            content = self._apply_translation(string[1], trans, content)
        self.compiled_template = content

    def _examine_content(self, content):
        """Peek into the template before any string is compiled.
        """
        return content

    def _get_source_strings(self):
        """Return the source strings of the resource."""
        return SourceEntity.objects.filter(
            resource=self.resource
        ).values_list(
            'id', 'string_hash'
        )

    def _post_compile(self):
        """Do any work after the compilation process."""
        pass

    def _pre_compile(self):
        """Do any work before compiling the translation."""
        pass

    def _replace_translation(self, original, replacement, text):
        """Put the translation to the text.

        Do a search and replace inside ``text`` and replaces all
        occurrences of ``original`` with ``replacement``.

        TODO: use string.replace instead of re.sub.
        """
        return re.sub(re.escape(original), replacement, text)


class DecoratorBuilder(object):
    """Builder for decorating the translation."""

    def __init__(self, *args, **kwargs):
        """Set the escape function to use."""
        self._escape = kwargs.get('escape_func', self._default_escape)

    def __call__(self, translation):
        """Decorate a translation.
        Args:
            translation: The translation string.
        Returns:
            The decorated translation.
        """
        raise NotImplementedError

    def _default_escape(self, s):
        """Default escape function."""
        return s


class NormalDecoratorBuilder(DecoratorBuilder):
    """Just escape the translation."""

    def __call__(self, translation):
        """Escape the string first."""
        return self._escape(translation)


class PseudoDecoratorBuilder(DecoratorBuilder):
    """Pseudo-ize the translation."""

    def __init__(self, pseudo_func, *args, **kwargs):
        """Set the pseudo function to use."""
        self._pseudo_decorate = pseudo_func
        super(PseudoDecoratorBuilder, self).__init__(args, kwargs)

    def __call__(self, translation):
        """Use the pseudo function."""
        return self._pseudo_decorate(self._escape(translation))


class EmptyDecoratorBuilder(DecoratorBuilder):
    """Use an empty translation."""

    def __call__(self, translation):
        """Return an empty string."""
        return ""


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
        raise NotImplementedError


class AllTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch all translations."""

    def __call__(self, source_entities):
        """Get the translation strings that match the specified
        source_entities.
        """
        res = {}
        translations = Translation.objects.filter(
            source_entity__in=source_entities, language=self.language, rule=5
        ).values_list(
            'source_entity_id', 'string'
        ).iterator()
        return dict(translations)


class EmptyTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch no translations."""

    def __init__(self, *args, **kwargs):
        super(EmptyTranslationsBuilder, self).__init__(None, None)

    def __call__(self, source_entities):
        """Return an empty dictionary."""
        return {}


class ReviewedTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch only reviewed strings."""

    def __call__(self, source_entities):
        """Get the translation strings that match the specified source_entities
        and have been reviewed.
        """
        translations = Translation.objects.filter(reviewed=True,
            source_entity__in=source_entities, language=self.language, rule=5
            ).values_list('source_entity_id', 'string').iterator()
        return dict(translations)

class SourceTranslationsBuilder(TranslationsBuilder):
    """Builder to use source strings in case of missing strings."""

    def __call__(self, source_entities):
        """Get the translation strings that match the specified
        source entities. Use the source strings for the missing
        ones.
        """
        raise NotImplementedError
