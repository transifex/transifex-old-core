# -*- coding: utf-8 -*-
from django import template

register = template.Library()

@register.inclusion_tag("upload_manager")
def upload_manager(target_object):
    print " target_object:", target_object
    