from django.contrib.auth.models import Group

def add_user_to_registered_group(sender, **kwargs):
    """
    Add any user created on the system to the `registered` group.

    This signal must be called by the post_save signal from the Profile class.
    """
    if 'created' in kwargs and kwargs['created'] is True: 
        profile = kwargs['instance']
        group, created = Group.objects.get_or_create(name='registered')
        profile.user.groups.add(group)
