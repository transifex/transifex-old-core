# -*- coding: utf-8 -*-
import datetime
from django.db.models.signals import post_save
from django.db.models.fields.related import OneToOneField
from django.db import models
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class IntegerTupleField(models.CharField):
    """
    A field type for holding a tuple of integers. Stores as a string
    with the integers delimited by colons.
    """
    __metaclass__ = models.SubfieldBase

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.RegexField,
            # We include the final comma so as to not penalize Python
            # programmers for their inside knowledge
            'regex': r'^\((\s*[+-]?\d+\s*(,\s*[+-]?\d+)*)\s*,?\s*\)$',
            'max_length': self.max_length,
            'error_messages': {
                'invalid': _('Enter 0 or more comma-separated integers '
                    'in parentheses.'),
                'required': _('You must enter at least a pair of '
                    'parentheses containing nothing.'),
            },
        }
        defaults.update(kwargs)
        return super(IntegerTupleField, self).formfield(**defaults)
    
    def to_python(self, value):
        if type(value) == tuple:
            return value
        if type(value) == unicode and value.startswith('(') and \
            value.endswith(')'):
            return eval(value)
        if value == '':
            return ()
        if value is None:
            return None
        return tuple(int(x) for x in value.split(u':'))
        
    def get_db_prep_value(self, value):
        if value is None:
            return None
        return u':'.join(unicode(x) for x in value)
        
    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type == 'exact':
            return [self.get_db_prep_value(value)]
        else:
            raise TypeError('Lookup type %r not supported' %
                lookup_type)
    
    def value_to_string(self, obj):
        return self.get_db_prep_value(obj)