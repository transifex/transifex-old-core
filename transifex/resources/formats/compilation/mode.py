# -*- coding: utf-8 -*-

"""
Modes for compiling a translation.
"""


class _Mode(object):
    """Class to suggest, what a translation is downloaded for.

    This class **should not** be used directly by the user. He should
    use the *constants* defined afterwards.

    The class has a ``_value`` variable, which is a set that holds
    *features* chosed.

    Each type of *feature* should define a value that is the next
    available power of two.
    """

    # use slots to save memory
    __slots__ = ('_value', )

    def __init__(self, value=set([0])):
        """Set the initial mode of the object."""
        self._value = value

    def __or__(self, other):
        """Combine modes."""
        return _Mode(self._value | other._value)

    def __contains__(self, item):
        """Return whether the mode contains the specified state."""
        return item._value <= self._value

    def __unicode__(self):
        return u'<Mode %s>' % self._value


VIEW = _Mode(value=set([0]))
TRANSLATE = _Mode(value=set([1]))
REVIEWED = _Mode(set([2]))
