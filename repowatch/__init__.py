from django.core.mail import send_mail
from django.template import loader, Context

class WatchException(Exception):
    pass

#TODO: patch update routine to compare revs

def send_email(site, component, user, repo_changed, files):
    """
    Sends email to a watcher for a specific component
    """
    context = Context({'component': component.name,
        'first_name': user.first_name, 'hostname': site.domain,
        'url': 'http://%s/' % site.domain, 'files': files,
        'repo_changed': repo_changed})
    subject = loader.get_template('templates/subject.tmpl').render(
        context)
    message = loader.get_template('templates/body.tmpl').render(
        context)
    from_address = 'Transifex <donotreply@%s>' % site.domain
    send_mail(subject, message, from_address, [user.email])
