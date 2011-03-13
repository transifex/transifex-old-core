from django.conf import settings
from django.contrib.auth.models import Group, SiteProfileNotAvailable
from django.core.exceptions import ImproperlyConfigured
from django.db import models, transaction
from transifex.txcommon.log import logger

if not settings.AUTH_PROFILE_MODULE:
    raise SiteProfileNotAvailable
try:
    app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
    Profile = models.get_model(app_label, model_name)
except (ImportError, ImproperlyConfigured):
    raise SiteProfileNotAvailable
if not Profile:
    raise SiteProfileNotAvailable

@transaction.commit_manually
def add_user_to_registered_group(sender, **kwargs):
    """
    Add any user created on the system to the `registered` group.

    This signal must be called by the post_save signal from the User class.
    This signal also creates a public profile for the user if it does not exist.
    """
    if 'created' in kwargs and kwargs['created'] is True:

        user = kwargs['instance']

        # Add user to registered group
        group, created = Group.objects.get_or_create(name='registered')
        user.groups.add(group)

        sid = transaction.savepoint()

        # Create Public Profile
        try:
            profile, created = Profile.objects.get_or_create(user=user)
            profile.save()
            transaction.savepoint_commit(sid)
        except:
            logger.debug("User profile not created.")
            transaction.savepoint_rollback(sid)

    transaction.commit()
