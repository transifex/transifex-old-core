"""
This module contains a model representation
of the review request. The following definitions are used:

POReviewRequest: A file under review entry in the database.
"""

import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from projects.models import Component
from transifex.translations.models import POFile 
from teams.models import Team
from translations.models import Language

class POReviewRequestManager(models.Manager):

    def open_reviews(self):
        """ Return a list of active Requests. """
        return self.filter(status='O')

    def closed_reviews(self):
        """ Return a list of inactive Requests. """
        return self.filter(status='C')

class POReviewRequest(models.Model):
    """A POReviewRequest is a review representation of a PO file.
    
    The review refers to a specific PO file. It can have two statuses:
    "open" or "closed". By default the PO review is created as "open".
    The reviewer marks it as "closed", if he accepted or rejected the 
    translation. This is indicated to the resolution field.
    When a reviewer approves the translation, the review resolution takes 
    the values 'Accepted'. Otherwise, if he wants to reject it, 
    it is marked as 'Rejected'. The resolution 'Null' vakue is used as 
    the default. The po file can also be commented and the comments are 
    stored in this model.
     
    """
    
    STATUS_CHOICES = (('O', _('Open')),
                     ('C', _('Closed')),)

    RESOLUTION_CHOICES = (('N', _('Null')),
                     ('A', _('Accepted')),
                     ('R', _('Rejected')),)

    description = models.CharField(max_length=300, blank=True, null=True,
        help_text="Describe your review request.")
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='O',
        help_text=_("The review's status (open, closed, etc.)"))
    resolution = models.CharField(max_length=1, choices=RESOLUTION_CHOICES,
        default='N', help_text=_("The review's resolution/closing state."))
    created_on = models.DateTimeField(auto_now_add=True,
        help_text=_("Date and time of creation"))
    last_updated = models.DateTimeField(auto_now=True,
        help_text=_("Date and time of last update"))

    file_name = models.CharField(max_length=200, editable=False,
        help_text=_("The review file name"), )
    target_filename = models.CharField(null=False, max_length=255, editable=False,
        help_text=_("The path of the target file which will be used on submission"), )
    lang_code = models.CharField(null=False, max_length=200)

    # Relations
    component = models.ForeignKey(Component, verbose_name=_('Component'),
                                  related_name='reviews')
#    pofile = models.ForeignKey(POFile, verbose_name=_('PO File'),
#                               related_name='reviews',)
    author = models.ForeignKey(User)
    scorers = models.ManyToManyField(User, through='ReviewLike',
        related_name='scored_reviews')

    # Managers
    objects = POReviewRequestManager()

    def __unicode__(self):
        return u"%(component)s (%(id)s)" % {
            'component': self.component,
            'id': self.id,
            }

    class Meta:
        verbose_name = _('Review Request')
        verbose_name_plural = _('Review Requests')
        ordering  = (_('-created_on'),)
        get_latest_by = _('created_on')


    @property
    def is_closed(self):
        return (self.status == 'C')

    @property
    def is_open(self):
        return (self.status == 'O')

    @property
    def full_review_filename(self):
        return '%d.%s' % (self.id, self.file_name)
        
    @property
    def file_url(self):
        return settings.REVIEWS_URL + self.full_review_filename

    @property
    def file_path(self):
        return settings.REVIEWS_ROOT + self.full_review_filename
    
    @property
    def language(self):
        try:
            return Language.objects.by_code_or_alias(self.lang_code)
        except Language.DoesNotExist:
            pass

    @property
    def team(self):
        try:
            return Team.objects.get(project__pk= self.component.project.pk,
                language__code=self.lang_code)
        except Team.DoesNotExist:
            pass

    @property
    def score(self):
        return ReviewLike.objects.review_score(self)


class ReviewLikeManager(models.Manager):
    def review_score(self, review):
        sum_ = 0
        for r in ReviewLike.objects.filter(reviewrequest=review):
            if r.like:
                sum_ += 1
            else:
                sum_ -= 1
        return sum_

class ReviewLike(models.Model):
    """Mark a review as like or dislike for a specific user."""

    like = models.NullBooleanField(default=None)
    reviewrequest = models.ForeignKey(POReviewRequest)
    user = models.ForeignKey(User)
    
    objects = ReviewLikeManager()

