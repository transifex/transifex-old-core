# -*- coding: utf-8 -*-
"""
Validator classes for individual strings.
"""

import re
from polib import escape        # TODO: Fix the regex
from django.conf import settings
from django.utils.translation import ugettext as _
from transifex.txcommon import import_to_python


class ValidationError(Exception):
    pass


class BaseValidator(object):
    """Base class for validators.

    Implements the decorator pattern.
    """

    def __init__(self, source_language=None, target_language=None, rule=None):
        self.slang = source_language
        self.tlang = target_language
        self.rule = rule

    def __call__(self, old, new):
        """Validate the `new` translation against the `old` one.

        No checks are needed for deleted translations

        Args:
            old: The old translation.
            new: The new translation.
        Raises:
            A ValidationError with an appropriate message.
        """
        if not new or not self.precondition():
            return
        self.validate(old, new)

    def precondition(self):
        """Check whether this validator is applicable to the situation."""
        return True

    def validate(self, old, new):
        """Actual validation method.

        Subclasses must override this method.

        Args:
            old: The old translation.
            new: The new translation.
        Raises:
            A ValidationError with an appropriate message.
        """
        pass


class PluralOnlyValidator(BaseValidator):
    """Validator to specialize handling of pluralized strings.

    Ignore check for singular.
    """

    def precondition(self):
        return self.rule != 1 and\
                super(PluralOnlyValidator, self).precondition()


class SpaceValidator(BaseValidator):
    """Validator that checks if the translation is just spaces."""

    def validate(self, old, new):
        if len(new.strip()) == 0:
            raise ValidationError(
                _("Translation string only contains whitespaces.")
            )


class MatchingBracketsValidator(BaseValidator):
    """Validator that checks if the number of brackets match between
    the two translations.
    """
    bracket_chars = '[{()}]'

    def validate(self, old, new):
        for c in self.bracket_chars:
            if new.count(c) != old.count(c):
                raise ValidationError(
                    _("Translation string doesn't contain the same "
                      "number of '%s' as the source string." % c)
                )


class UrlsValidator(BaseValidator):
    """Validator that checks if urls have been preserved in the
    translation.
    """

    urls = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|'
                      '(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )

    def validate(self, old, new):
        for url in self.urls.findall(old):
            if url not in new:
                raise ValidationError(
                    _("The following url is either missing from the"
                      " translation or has been translated: '%s'." % url)
                )


class EmailAddressesValidator(BaseValidator):
    """Validator that checks if the email addresses have been preserved in
    the translation.
    """

    emails = re.compile("([\w\-\.+]+@[\w\w\-]+\.+[\w\-]+)")

    def validate(self, old, new):
        for email in self.emails.findall(old):
            if email not in new:
                raise ValidationError(
                    _("The following email is either missing from the"
                      " translation or has been translated: '%s'." % email)
                )


class NewLineAtBeginningValidator(BaseValidator):
    """Validator that checks if a new line at the beginning
    has been preserved.
    """

    def validate(self, old, new):
        old_has_newline = old[0] == '\n'
        new_has_newline = new[0] == '\n'
        if old_has_newline != new_has_newline:
            if old_has_newline:
                msg = _("Translation must start with a newline (\\n)")
            else:
                msg = _("Translation should not start with a newline (\\n)")
            raise ValidationError(msg)


class NewLineAtEndValidator(BaseValidator):
    """Validator that checks if a new line at the end has been
    preserved.
    """

    def validate(self, old, new):
        old_has_newline = old[-1] == '\n'
        new_has_newline = new[-1] == '\n'
        if old_has_newline != new_has_newline:
            if old_has_newline:
                msg = _("Translation must end with a newline (\\n)")
            else:
                msg = _("Translation should not end with a newline (\\n)")
            raise ValidationError(msg)


class NumbersValidator(BaseValidator):
    """Validator that checks that numbers have been preserved in the
    translation.
    """

    numbers = re.compile("[-+]?[0-9]*\.?[0-9]+")

    def validate(self, old, new):
        for num in self.numbers.findall(old):
            if num not in new:
                raise ValidationError(
                    _("Number %s is in the source string but not "
                      "in the translation." % num)
                )


class PrintfFormatNumberValidator(BaseValidator):
    """Validator that checks that the number of printf formats specifiers
    is the same in the translation.

    This is valid only if the plurals in the two languages are the same.
    """

    printf_re = re.compile(
        '%((?:(?P<ord>\d+)\$|\((?P<key>\w+)\))?(?P<fullvar>[+#-]*(?:\d+)?'\
            '(?:\.\d+)?(hh\|h\|l\|ll)?(?P<type>[\w%])))'
    )

    def precondition(self):
        """Check if the number of plurals in the two languages is the same."""
        return self.tlang.nplurals == self.slang.nplurals and \
                super(PrintfFormatNumberValidator, self).precondition()

    def validate(self, old, new):
        old_matches = list(self.printf_re.finditer(old))
        new_matches = list(self.printf_re.finditer(new))
        if len(old_matches) != len(new_matches):
            raise ValidationError(
                _('The number of arguments seems to differ '
                  'between the source string and the translation.')
            )


class PrintfFormatPluralizedNumberValidator(PluralOnlyValidator, \
                                                PrintfFormatNumberValidator):
    """Validator that checks that the number of arguments are equal
    in case of plurals.

    Ignores the check in case of the singular grammatical number.
    """
    pass


class PrintfFormatSourceValidator(BaseValidator):
    """Validator that checks printf-format specifiers in the source string
    are preserved in the translation.
    """

    printf_re = re.compile(
        '%((?:(?P<ord>\d+)\$|\((?P<key>\w+)\))?(?P<fullvar>[+#-]*(?:\d+)?'\
            '(?:\.\d+)?(hh\|h\|l\|ll)?(?P<type>[\w%])))'
    )

    def validate(self, old, new):
        old_matches = list(self.printf_re.finditer(old))
        new_matches = list(self.printf_re.finditer(new))
        old = escape(old)
        new = escape(new)
        for pattern in old_matches:
            if pattern.group(0) not in new:
                raise ValidationError(
                    _('The expression \'%s\' is not present in the'
                      'translation.' % pattern.group(0))
                )


class PrintfFormatPluralizedSourceValidator(PluralOnlyValidator, \
                                                PrintfFormatSourceValidator):
    """Validator that checks printf-format specifiers in the source string
    are preserved in the translation.

    Ignores the check in case of the singular grammatical number.
    """
    pass


class PrintfFormatTranslationValidator(BaseValidator):
    """Validator that checks printf-format specifiers in the translation
    string show up in the source string.
    """

    printf_re = re.compile(
        '%((?:(?P<ord>\d+)\$|\((?P<key>\w+)\))?(?P<fullvar>[+#-]*(?:\d+)?'\
            '(?:\.\d+)?(hh\|h\|l\|ll)?(?P<type>[\w%])))'
    )

    def validate(self, old, new):
        old = escape(old)
        new = escape(new)
        old_matches = list(self.printf_re.finditer(old))
        new_matches = list(self.printf_re.finditer(new))
        for pattern in new_matches:
            if pattern.group(0) not in old:
                raise ValidationError(
                    _('The expression \'%s\' is not present '
                      'in the source string.' % pattern.group(0))
                )


def create_error_validators(i18n_type):
    """Create a suitable errors validator for the specific i18n type."""
    return _create_validators(i18n_type, 'I18N_ERROR_VALIDATORS')


def create_warning_validators(i18n_type):
    """Create a suitable warnings validator for the specific i18n type."""
    return _create_validators(i18n_type, 'I18N_WARNING_VALIDATORS')


def _create_validators(i18n_type, type_):
    """Create a generator of validators for the specific i18n_type and
    errors/warning check we need.

    Args:
        i18n_type: The i18n type forthe validators.
        type_: A string with the name of the type of the validators we need.
            Currently, either I18N_ERROR_VALIDATORS or I18N_WARNING_VALIDATOR.
    Returns:
        A generator with validator objects.
    """
    type_validators = getattr(settings, type_)
    if i18n_type in type_validators:
        key = i18n_type
    else:
        key = 'DEFAULT'
    return (import_to_python(klass) for klass in type_validators[key])
