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


class ValidTarBallUrl(CharField):
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super(ValidTarBallUrl, self).__init__(max_length, min_length, *args, **kwargs)

    def clean(self, value):
        value = super(ValidTarBallUrl, self).clean(value)
        if (value.startswith('http://') or value.startswith('ftp://')):
            if value.endswith('tar.gz') or value.endswith('.tgz'):
                return value
            else:
                raise ValidationError(_('The root url does not point to a '
                                        '.tar.gz or .tgz file'))
        else:
            raise ValidationError(_('The root url must start with http:// or '
                                    'ftp://'))
        return value
