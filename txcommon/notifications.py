# -*- coding: utf-8 -*-
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from notification.models import ObservedItem, is_observing

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