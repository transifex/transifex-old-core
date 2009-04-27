from projects import signals
from txcommon.log import logger

def _updatecomponents(project):
    """
    Look through the components for a specific project and update them based 
    on the project changes
    """
    from projects.models import Component

    collection_query = project.collections.values('pk').query
    for c in Component.objects.filter(project__id=project.id):
        releases = c.releases.exclude(collection__id__in=collection_query)
        for release in releases:
            logger.debug("Release '%s' removed from '%s'" % (release, c))
            c.releases.remove(release)
        c.save()

def _projectpostm2mhandler(sender, **kwargs):
    if 'instance' in kwargs:
        _updatecomponents(kwargs['instance'])

signals.post_proj_save_m2m.connect(_projectpostm2mhandler)