# -*- coding: utf-8 -*-

"""
Factories for compilers.
"""

from transifex.resources.formats.compilation.decorators import \
        NormalDecoratorBuilder, PseudoDecoratorBuilder, EmptyDecoratorBuilder
from transifex.resources.formats.compilation.builders import \
        AllTranslationsBuilder, EmptyTranslationsBuilder, \
        ReviewedTranslationsBuilder, SourceTranslationsBuilder
from .mode import TRANSLATE, REVIEWED


class CompilerFactory(object):
    """Factory to create compilers.

    This should be used as a mixin.
    """

    def construct_compiler(self, language, pseudo_type, mode):
        """Construct a compiler.

        Args:
            language: The language to use.
            pseudo_type: The pseudo_type to use.
            mode: The mode of the compilation.
        Returns:
            A suitable compiler.
        """
        raise NotImplementedError

    def _get_compiler(self):
        """Construct the compiler to use.

        We use by default ``cls.CompilerClass``. If a format does not have
        any special needs, we only need to set the ``CompilerClass``
        variable to the appropriate compiler subclass.

        Otherwise, a subclass should override this, so that it can
        choose the appropriate compiler.
        """
        return self.CompilerClass(resource=self.resource)

    def _get_translation_decorator(self, pseudo_type):
        """Choose the decorator to use.

        Override in subclasses, if you need to use a custom one for a
        specific format.

        Args:
            pseudo_type: The pseudo type chosen.
        Returns:
            An instance of the applier.
        """
        if pseudo_type is None:
            return NormalDecoratorBuilder(escape_func=self._escape)
        else:
            return PseudoDecoratorBuilder(
                escape_func=self._escape,
                pseudo_func=pseudo_type.compile
            )


class SimpleCompilerFactory(CompilerFactory):
    """Use translation string set as is."""

    def construct_compiler(self, language, pseudo_type, mode):
        """Construct a compiler that uses only the translations for the
        stringset.
        """
        tdec = self._get_translation_decorator(pseudo_type)
        tset = self._get_translation_setter(language, mode)
        compiler = self._get_compiler()
        compiler.translation_decorator = tdec
        compiler.translation_set = tset
        return compiler


    def _get_translation_setter(self, language, mode):
        """Get the translations builder.

        This is used to fetch the set of translations to be used in
        the compilation process. The default one is to fetch all
        translations.

        Subclasses should override this, if they need to use a different
        TransaltionsBuilder subclass.

        Args:
            language: The language for the translations.
            mode: The mode for the compilation.
        Returns:
            An instance of the apporpriate translations builder.
        """
        if REVIEWED in mode:
            return ReviewedTranslationsBuilder(self.resource, language)
        else:
            return AllTranslationsBuilder(self.resource, language)
