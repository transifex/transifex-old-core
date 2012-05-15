# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf import settings
from django.core.mail import send_mail
from datastores.txredis import TxRedis, redis_exception_handler
from .conf import INTERVAL


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
    r.expire(key, INTERVAL)
    return False


def _mail_user(name, email):
    """Email the user about the old client used."""

    subject = 'Transifex client in use is outdated'
    body = """Greetings %(username)s,

here at Transifex we constantly try to deliver more and better features to our
users.  We noticed that recently you used an outdated version of the client to
access Transifex.com.

If you would like to take advantage of all the new features that have been
implemented in the newer versions, you can always visit %(install_url)s for
instructions on how to install the latest version.

For any questions that you may have, feel free to contact us at
https://www.transifex.com/contact/

The Transifex team
https://www.transifex.com/""" % dict(
        username=name,
        install_url='http://bit.ly/txsetup'
        )

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
        if user.first_name and user.last_name:
            username = '%(first)s %(last)s' % dict(
                first=user.first_name,
                last=user.last_name,
                )
        else:
            username = user.username

        _mail_user(username, user.email)
