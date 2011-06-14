# -*- coding: utf-8 -*-

from django.utils.hashcompat import md5_constructor

def hash_tag(source_entity, context):
    """Calculate the md5 hash of the (source_entity, context)."""
    if type(context) == list:
        keys = [source_entity] + context
    else:
        keys = [source_entity, context]
    return md5_constructor(
        ':'.join(keys).encode('utf-8')
    ).hexdigest()
