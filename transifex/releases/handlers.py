from django.db.models import (get_model, signals)
from django.utils.translation import ugettext_lazy as _
from transifex.resources.models import Resource
from transifex.releases.models import RELEASE_ALL_DATA

Release = get_model('releases', 'Release')

def update_all_release(project):
    if project.resources.count():
        rel, rel_created = project.releases.get_or_create(
            slug=RELEASE_ALL_DATA['slug'],
            defaults={'name': RELEASE_ALL_DATA['name'],
                      'description': RELEASE_ALL_DATA['description'],})
        rel.resources = project.resources.all()
        return rel
    else:
        return None


def release_all_push(sender, instance, **kwargs):
    """
    Append newly created resource to the 'all' release.
    
    Add newly created resources to the special release called 'All Resources',
    which contains all the resources for a project at all times. If it is the
    first create the release when the first resource is added to the project.

    Called every time a resource is created.
    """

    resource = instance
    created = kwargs['created']
    if created:
        update_all_release(resource.project)


def release_all_pop(sender, instance, **kwargs):
    """
    Remove newly deleted resource to the 'all' release.
    
    Remove newly deleted resources from the special release called
    'All Resources'. Delete the release when the last resource is added to it.

    Called every time a resource is deleted.
    """

    resource = instance
    try:
        rel = resource.project.releases.get(slug=RELEASE_ALL_DATA['slug'])
    except Release.DoesNotExist:
        rel = None
    if rel and not rel.resources.count():
        rel.delete()

# Connect handlers to populate 'all' release (more info in handler docstrings):
signals.post_save.connect(release_all_push, sender=Resource)
signals.post_delete.connect(release_all_pop, sender=Resource)

