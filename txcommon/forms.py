import re

from django.forms import CharField, ValidationError
from django.utils.translation import ugettext_lazy as _

class ValidRegexField(CharField):
    def __init__(self, **kwargs):
        super(ValidRegexField, self).__init__(**kwargs)

    def clean(self, value):
        try:
            return re.compile(value).pattern
        except re.error, e:
            raise ValidationError(_('Enter a valid regular expression.'))
