# -*- coding: utf-8 -*-

"""
The compilation package for Transifex.

This package hosts the code to compile a template of a resource to
a translation file.
"""

from __future__ import absolute_import
from .compilers import Compiler
from .decorators import NormalDecoratorBuilder, PseudoDecoratorBuilder, \
        EmptyDecoratorBuilder
from .builders import AllTranslationsBuilder, EmptyTranslationsBuilder, \
        ReviewedTranslationsBuilder, SourceTranslationsBuilder
from .factories import SimpleCompilerFactory, FillEmptyCompilerFactory
