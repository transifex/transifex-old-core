from django import template
from django.conf import settings

register = template.Library()

WEBTRANS_MAX_STRINGS = getattr(settings, 'WEBTRANS_MAX_STRINGS', None)

@register.filter
def fuzzy_field(field, form):
    """Return the related fuzzy_field for a msgstr_field."""
    return form['fuzzy_field_%s' % field.name.split('msgstr_field_')[1]]

@register.filter
def webtrans_is_under_max(number):
    """
    Return True if `number` is smaller or equals than the WEBTRANS_MAX_STRINGS 
    set up in the settings. Case WEBTRANS_MAX_STRINGS is not defined, there is 
    no limit.
    """
    if not WEBTRANS_MAX_STRINGS:
        return True
    elif number <= WEBTRANS_MAX_STRINGS:
        return True
    return False
