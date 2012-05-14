# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.mail import send_mail
from datastores.txredis import TxRedis, redis_exception_handler


_LIFE_TIME = 24 * 60 * 60

def _cache_key(email):
    """Key to use in Redis for emails."""
    return 'client:notify:%s' % email


def delete_from_cache(email):
    """Delete an email from the redis cache."""
    r = TxRedis()
    r.delete(_cache_key(email))


@redis_exception_handler
def _mail_already_sent(email):
    """
    Check, whether the user has already been notified.

    Return True, if a notification to the user has already been sent today.
    """
    key = _cache_key(email)
    r = TxRedis()
    if r.exists(key):
        return True
    r.set(key, '')
    r.expire(key, _LIFE_TIME)
    return False


def _mail_user(email):
    """Email the user about the old client used."""
    subject = ''
    body = ''
    sender = settings.DEFAULT_FROM_EMAIL
    receipients = [email, ]
    send_mail(subject, body, sender, receipients, fail_silently=True)



def notify_user(user):
    """
    Notify the user that he uses an old version of the client.

    Send him an email, if needed.
    """
    if not user.email:
        return

    if not _mail_already_sent(user.email):
        _mail_user(user.email)
