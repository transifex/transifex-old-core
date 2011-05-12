# -*- coding: utf-8 -*-

from django.utils.hashcompat import md5_constructor

def hash_tag(source_entity, context):
    """Calculate the md5 hash of the (source_entity, context)."""
    return md5_constructor(
        ':'.join([source_entity, context]).encode('utf-8')
    ).hexdigest()
