from django.conf import settings
from django.contrib.auth.models import Group, SiteProfileNotAvailable
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.signals import post_save

if not settings.AUTH_PROFILE_MODULE:
    raise SiteProfileNotAvailable
try:
    app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
    Profile = models.get_model(app_label, model_name)
except (ImportError, ImproperlyConfigured):
    raise SiteProfileNotAvailable
if not Profile:
    raise SiteProfileNotAvailable

def user_registering(sender, **kwargs):
    """
    Add any user created on the system to the `registered` group and also 
    creates a profile to him/her.

    This signal must be called by the post_save signal from the User class.
    """
    if 'created' in kwargs and kwargs['created'] is True: 
        user = kwargs['instance']
        # Create Public Profile
        profile, created = Profile.objects.get_or_create(user=user)
        # Add user to registered group
        group, created = Group.objects.get_or_create(name='registered')
        user.groups.add(group)

post_save.connect(add_user_to_registered_group, sender=User)
