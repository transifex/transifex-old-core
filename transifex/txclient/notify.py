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


def _mail_user(username, email):
    """Email the user about the old client used."""
    subject = 'Transifex client in use is outdated'
    body = """Greetings %(username)s,

here at Transifex we constantly try to deliver more and better features to our users.
We noticed that recently you used our command line client to access transifex.
Unfortunately, the version of the client that you used is outdated.

If you would like to take advantage of all the new features that have been implemented
in the newer versions, you can always visit %(install_url)s for a reminder on updating
the client.

For any questions that you may have, feel free to contact us at https://www.transifex.com/contact/

Always at your service,
the transifex team.
https://www.transifex.com/""" % dict(username=username, install_url='http://bit.ly/txsetup')

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
        _mail_user(user.username, user.email)
