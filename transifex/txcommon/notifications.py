# -*- coding: utf-8 -*-
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from notification.models import (ObservedItem, is_observing, send)

def is_watched_by_user_signal(obj, user, signal=None):
    """
    Return a boolean value if an object is watched by an user or not

    It is possible also verify if it is watched by a user in a specific 
    signal, passing the signal as a second parameter
    """
    if signal:
        return is_observing(obj, user, signal)

    if isinstance(user, AnonymousUser):
        return False
    try:
        ctype = ContentType.objects.get_for_model(obj)
        observed_items = ObservedItem.objects.get(content_type=ctype,
                                                object_id=obj.id, user=user)
        return True
    except ObservedItem.DoesNotExist:
        return False
    except ObservedItem.MultipleObjectsReturned:
        return True


# Overwritting this function temporarily, until the upstream patch
# http://github.com/jezdez/django-notification/commit/a8eb0980d2f37b799ff55dbc3a386c97ad479f99
# be accepted on http://github.com/pinax/django-notification
def send_observation_notices_for(observed, signal='post_save', extra_context=None):
    """
    Send a notice for each registered user about an observed object.
    """
    observed_items = ObservedItem.objects.all_for(observed, signal)
    for item in observed_items:
        if extra_context is None:
            extra_context = {}

        context = {
            "observed": item.observed_object,
        }
        context.update(extra_context)

        send([item.user], item.notice_type.label, context)
    return observed_items
