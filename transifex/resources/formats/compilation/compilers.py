# -*- coding: utf-8 -*-

"""
Compiler classes.

Classes that handle compiling a template.
"""

from transifex.resources.models import SourceEntity
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
        """
        return text.replace(original, replacement)

