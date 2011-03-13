# -*- coding: utf-8 -*-
import datetime
from django.contrib.auth.models import User
from django.db.models.fields.related import OneToOneField
from django.db.models.signals import post_save
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from userprofile.models import BaseProfile

Language = models.get_model('languages', 'Language')

GENDER_CHOICES = ( ('F', _('Female')), ('M', _('Male')),)

def get_profile_or_user(user):
    """
    Return the Profile of the user or the User itself in the case where
    the application is using app simpleauth.

    ``user`` must be a django.contrib.auth.models.User based instance
    """
    try:
        return Profile.objects.get(user__pk=user.pk)
    except Profile.DoesNotExist:
        return user

class Profile(BaseProfile):
    """
    Profile class to used as a base for the django-profile app
    """
    firstname = models.CharField(_('First name'), max_length=255, blank=True)
    surname = models.CharField(_('Surname'), max_length=255, blank=True)

    native_language = models.ForeignKey(Language, blank=True,
        verbose_name=_('Native Language'), null=True)
    blog = models.URLField(_('Blog'), blank=True)
    linked_in = models.URLField(_('LinkedIn'), blank=True)
    twitter = models.URLField(_('Twitter'), blank=True)
    about = models.TextField(_('About yourself'), max_length=140, blank=True,
        help_text=_('Short description of yourself (140 chars).'))
    looking_for_work = models.BooleanField(_('Looking for work?'), default=False)

def exclusive_fields(inmodel, except_fields=[]):
    '''
    Returns a generator that yields the fields that belong only to the
    given model descendant

    ``except_fields`` is a list that allows to skip some fields based on theirs
    names
    '''
    for field, model in inmodel._meta.get_fields_with_model():
        if field.name in except_fields:
            yield field
        # Field belongs to an ancestor
        if model is not None:
            continue
        # Field relates to an ancestor
        if isinstance(field, OneToOneField) and (field.rel.to in
            inmodel.__bases__):
            continue
        yield field

def inclusive_fields(inmodel, except_fields=[]):
    '''
    Returns a generator that yields the fields that belong to the given
    model descendant or any of its ancestors

    ``except_fields`` is a list that allows to skip some fields based on theirs
    names
    '''
    for field, model in inmodel._meta.get_fields_with_model():
        # Field relates to the parent of the model it's on
        if isinstance(field, OneToOneField):
            # Passed model
            if (model is None) and (field.rel.to in inmodel.__bases__):
                continue
            # Ancestor model
            if (model is not None) and (field.rel.to in model.__bases__):
                continue
        if field.name in except_fields:
            continue
        yield field

# Signal Registration
import listeners
post_save.connect(listeners.add_user_to_registered_group, sender=User)
