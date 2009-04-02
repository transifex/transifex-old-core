import operator
import itertools

from django.core.mail import send_mail
from django.template import loader, Context
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _

from projects import signals
from txcommon.log import logger

class WatchException(StandardError):
    pass

def _send_email(site, component, users, repo_changed, files):
    """
    Send email to watchers for a specific component
    
    site: django.contrib.sites.models.Site for the site sending
        the message
    component: projects.models.Component that had the change
    users: django.contrib.auth.models.User list that set the watch
    repo_change: Whether or not the repo had a global change
    files: List of paths being watched that changed
    """
    for user in users:
        context = Context({'component': component.name,
            'project': component.project.name,
            'first_name': (user.first_name or user.username), 
            'hostname': 'http://%s' % site.domain,
            'url': 'http://%s%s' % (site.domain, component.get_absolute_url()),
            'files': files,
            'repo_changed': repo_changed})
        subject = loader.get_template('subject.tmpl').render(
            context).strip('\n')
        message = loader.get_template('body.tmpl').render(
            context)
        from_address = 'Transifex <donotreply@%s>' % site.domain
        send_mail(subject, message, from_address, [user.email])

def _findchangesbycomponent(component):
    """
    Looks through the watches for a specific component and
    e-mails the users watching it
    """
    from repowatch.models import Watch
    watches = Watch.objects.filter(component=component)
    repochanged = False
    changes = []
    for watch in watches:
        try:
            newrev = component.get_rev(watch.path)
            logger.error('repowatch: old: %s, new: %s' % (watch.rev,
                newrev))
            if newrev != watch.rev:
                if not watch.path:
                    repochanged = True
                else:
                    changes.append((watch.user.all(), watch.path))
                watch.rev = newrev
                watch.save()
        except ValueError:
            continue    
    if changes:
        changes.sort(key=operator.itemgetter(0))
        for usergroup in itertools.groupby(changes,
            key=operator.itemgetter(0)):
            _send_email(Site.objects.get_current(), component,
                usergroup[0], repochanged, [change[1] for change
                in usergroup[1]])

def _compposthandler(sender, **kwargs):
    if 'instance' in kwargs:
        _findchangesbycomponent(kwargs['instance'])

signals.post_comp_prep.connect(_compposthandler)

watch_titles = {
    'watch_add_title': _('Watch this file'),
    'watch_remove_title': _('Stop watching this file'),
}
