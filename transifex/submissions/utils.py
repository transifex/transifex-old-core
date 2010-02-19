"""
Functions related to email submission.

Called when in a project the submissions are enabled to maintainers email.
"""

import re
import traceback
from django.conf import settings
from django.core.mail import EmailMessage, MIMEBase
from django.template import loader, Context
from django.contrib.sites.models import Site
from transifex.txcommon.log import logger
from transifex.translations.lib.types.pot import run_msgfmt_check
from submissions import SubmitError

DEFAULT_MIME_TYPE = 'text/plain'
DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL')

current_site = Site.objects.get_current()

def msgfmt_error_send_mail(component, user, submitted_file, attachments,
    filename):
    """
    Send an e-mail to the user with submitted_file concerning component.

    This funcation handles the case where a file is submitted which
    does not pass correctness checks. To avoid losing work, the file
    will be emailed to the user as an attachment.

    This can happen both in the File Upload form, as well as in Lotte.
    """

    context = Context({
        'component': component.name,
        'project': component.project.name,
        'current_site': 'http://%s' % current_site.domain,
        'url': 'http://%s%s' % (current_site.domain, component.get_absolute_url()),
        'user': user,
        'filename': filename,
        'error_message': "",
        })

    res = run_msgfmt_check(submitted_file, with_exceptions=False)
    context['error_message'] = ("%s\n" % res['stderr'].replace('<stdin>',
                                                               filename))
    subject = loader.get_template('subject_error.tmpl').render(context)
    subject = subject.strip('\n')
    message = loader.get_template('body_error.tmpl').render(context)
    mail = EmailMessage(subject, message, DEFAULT_FROM_EMAIL, [user.email])
    for fieldname, attach in attachments.iteritems():
        for chunk in attach.chunks():
            mail.attach(create_attachment(attach.targetfile, chunk))
    mail.send()

def submit_by_email(component, attachments, sender):
    """Send email with attachement to all maintainers of a project."""

    context = Context({'component': component.name,
        'project': component.project.name,
        'current_site': 'http://%s' % current_site.domain,
        'url': 'http://%s%s' % (current_site.domain, component.get_absolute_url()),
        'translator': (sender.first_name or sender.username),
        'translator_email': sender.email})

    subject = loader.get_template('subject.tmpl').render(context).strip('\n')

    for maintainer in component.project.maintainers.all():
        context.update({'maintainer':(maintainer.first_name or
            maintainer.username)})
        message = loader.get_template('body.tmpl').render(context)

        try:
            mail = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL,
                [maintainer.email])
            for fieldname, attach in attachments.iteritems():
                for chunk in attach.chunks():
                    mail.attach(create_attachment(attach.targetfile, chunk))
            mail.send()
        except StandardError:
            logger.error(traceback.format_exc())
            raise SubmitError('Unable to submit file via email')

def decide_encoding(chunk):
    """
    Return the actual encoding of the attachement/chuck and its mimetype.

    Usually a po file contains a line in the following format
    "Content-Type: <MIMETYPE>; charset=<ENCODING>\n"
    This fuction tries to get those two values and return them. If any of those
    is missing and can not be found, it returns the default settings
    (text/plain and sites default encoding)

    Keyword arguments:
    chunk -- Usually a po file data.

    Returns:
    (encoding, mimetype) -- A tuple containing the string representation for
        the encoding and mimetype. Example: ('utf-8', 'text/plain')
    """
    enc_regex = re.compile(
        r'"?Content-Type:.+? charset=([\w_\-:\.]+)')
    mime_regex = re.compile(
        r'Content-Type:(.*?)(?:;|$)')
    result = enc_regex.search(chunk)
    if result:
        encoding = result.group(1).strip()
    else:
        encoding = settings.DEFAULT_CHARSET

    result =  mime_regex .search(chunk)
    if result:
        mimetype = result.group(1).strip()
    else:
        mimetype = DEFAULT_MIME_TYPE
    return (encoding, mimetype)

def create_attachment(filename, chunk):
    """
    Create the actual attachement.

    Firstly it calls decide_encoding to find the attachement/chunks encoding.
    Then it creates an attachement based on the files encoding/mimetype and
    the MIMEBase object to attach to the actual mail.

    Keyword arguments:
    filename -- The filename for the attachement.
    chunk -- The actual data that we want to transmit. Usually a po file data.

    Returns:
        object MIMEBase -- An attachement object
    """
    encoding, mimetype = decide_encoding(chunk)
    encoding = encoding or settings.DEFAULT_CHARSET
    basetype, subtype = mimetype.split('/', 1)
    attachment = MIMEBase(basetype, subtype)
    attachment.set_payload(chunk, encoding)
    attachment.add_header(
        'Content-Disposition', 'attachment',
        filename=filename)
    return attachment
