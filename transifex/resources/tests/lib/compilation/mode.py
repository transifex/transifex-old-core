# -*- coding: utf-8 -*-

from django.utils import unittest
from transifex.resources.formats.compilation.mode import _Mode, VIEW, \
        TRANSLATE, REVIEWED


class TestCompilationModes(unittest.TestCase):
    """Test the modes of compilation."""

    def test_combine(self):
        """Test that modes can be combined."""
        m1 = REVIEWED
        m2 = TRANSLATE
        m = m1 | m2
        self.assertEquals(m._value, m1._value | m2._value)

    def test_containment(self):
        """Test that the ``in`` operator works for modes."""
        m1 = REVIEWED
        m2 = TRANSLATE
        m = m1 | m2
        self.assertNotIn(VIEW, m)
        self.assertIn(TRANSLATE, m)
        self.assertIn(REVIEWED, m)

        m1 = VIEW
        m2 = REVIEWED
        m = m1 | m2
        self.assertIn(VIEW, m)
        self.assertIn(REVIEWED, m)
        self.assertNotIn(TRANSLATE, m)

        m = VIEW
        self.assertIn(VIEW, m)
        self.assertNotIn(TRANSLATE, m)
        self.assertNotIn(REVIEWED, m)
