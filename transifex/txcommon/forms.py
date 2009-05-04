import re

from django.forms import CharField, ValidationError
from django.utils.translation import ugettext_lazy as _

class ValidRegexField(CharField):
    def __init__(self, max_length=None, min_length=None, error_message=None, *args, **kwargs):
        super(ValidRegexField, self).__init__(max_length, min_length, *args, **kwargs)

    def clean(self, value):
        value = super(ValidRegexField, self).clean(value)
        try:
            return re.compile(value).pattern
        except re.error, e:
            raise ValidationError(_('Enter a valid regular expression.'))

