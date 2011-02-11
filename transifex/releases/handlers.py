from django.db.models import (get_model, signals)
from django.utils.translation import ugettext_lazy as _
from transifex.resources.models import Resource

Release = get_model('releases', 'Release')

RELEASE_DATA = {
    'slug': 'all-resources',
    'name': _('All Resources'),
    'description': _('An auto-managed release containing all resources.')}

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
        rel, rel_created = resource.project.releases.get_or_create(
            slug=RELEASE_DATA['slug'],
            defaults={'name': RELEASE_DATA['name'],
                      'description': RELEASE_DATA['description'],})
        rel.resources.add(resource)


def release_all_pop(sender, instance, **kwargs):
    """
    Remove newly deleted resource to the 'all' release.
    
    Remove newly deleted resources from the special release called
    'All Resources'. Delete the release when the last resource is added to it.

    Called every time a resource is deleted.
    """

    resource = instance
    rel = resource.project.releases.get(slug=RELEASE_DATA['slug'])
    rel.resources.remove(resource)
    if not rel.resources.count():
        rel.delete()

# Connect handlers to populate 'all' release (more info in handler docstrings):
signals.post_save.connect(release_all_push, sender=Resource)
signals.post_delete.connect(release_all_pop, sender=Resource)

