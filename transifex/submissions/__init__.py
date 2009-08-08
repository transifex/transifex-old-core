import traceback
from django.conf import settings
from django.core.mail import EmailMessage
from django.template import loader, Context
from django.contrib.sites.models import Site

from txcommon.log import logger

class SubmitError(StandardError):
    pass

def submit_by_email(component, attachments, sender):

    site = Site.objects.get_current()
    emails = [u.email for u in component.project.maintainers.all()]
    filenames = [at.targetfile for fn, at in attachments.iteritems()]

    context = Context({'component': component.name,
        'project': component.project.name,
        'current_site': 'http://%s' % site.domain,
        'url': 'http://%s%s' % (site.domain, component.get_absolute_url()),
        'translator': (sender.first_name or sender.username),
        'translator_email': sender.email})

    subject = loader.get_template('subject.tmpl').render(context).strip('\n')

    for maintainer in component.project.maintainers.all():

        context.update({'maintainer':(maintainer.first_name or maintainer.username)})
        message = loader.get_template('body.tmpl').render(context)

        try:
            mail = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, 
                [maintainer.email])
            for fieldname, attach in attachments.iteritems():
                for chunk in attach.chunks():
                    mail.attach(attach.targetfile, chunk, attach.content_type)
            mail.send()
        except StandardError, e:
            logger.error(traceback.format_exc())
            raise SubmitError('Unable to submit file via email')
