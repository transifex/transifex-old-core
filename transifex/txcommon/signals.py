from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save

def add_user_to_registered_group(sender, **kwargs):
    """
    Add any user created on the system to the `registered` group.

    This signal must be called by the post_save signal from the User class.
    """
    if 'created' in kwargs and kwargs['created'] is True: 
        user = kwargs['instance']
        group, created = Group.objects.get_or_create(name='registered')
        user.groups.add(group)

post_save.connect(add_user_to_registered_group, sender=User)