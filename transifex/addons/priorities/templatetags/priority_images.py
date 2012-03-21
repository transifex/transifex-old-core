# -*- coding: utf-8 -*-

from django import template
from django.utils.safestring import mark_safe


register = template.Library()

@register.filter
def priority_image_path(level):
    """Return the path to the appropriate image for the specified level."""
    return mark_safe("priorities/images/%s.png" % level)
