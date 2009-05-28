from django import template

register = template.Library()

@register.filter
def fuzzy_field(field, form):
    """Return the related fuzzy_field for a msgstr_field."""
    return form['fuzzy_field_%s' % field.name.split('msgstr_field_')[1]]
