"""
This module contains a model representation
of the review request. The following definitions are used:

POReviewRequest: A file under review entry in the database.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from transifex.translations.models import POFile

class POReviewRequestManager(models.Manager):
    def open_reviews(self):
        """ Return a list of active Requests. """
        return self.filter(status='O')

class POReviewRequest(models.Model):
    """A POReviewRequest is a review representation of a PO file.
    
    The review refers to a specific PO file. It can have two statuses:
    "open" or "closed". By default the PO review is created as "open".
    The reviewer marks it as "closed", if he accepted or rejected the 
    translation. This is indicated to the resolution field.
    the file can be commented. When a reviewer approves the translation,
    the review resolution. Otherwise, it 
    is rejected.
     
    """
    
    STATUS_CHOICES = (('O', 'Open'),
                     ('C', 'Closed'),)

    RESOLUTION_CHOICES = (('N', 'Null'),
                     ('A', 'Accepted'),
                     ('R', 'Rejected'),)

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='O',
        help_text="The review's status (open, closed, etc.)")
    resolution = models.CharField(max_length=1, choices=RESOLUTION_CHOICES,
        default='N', help_text="The review's resolution/closing state.")    
    created_on = models.DateTimeField(auto_now_add=True, 
        help_text="Date and time of creation")
    last_updated = models.DateTimeField(auto_now=True, 
        help_text="Date and time of last update")

    # Relations
    pofile = models.ForeignKey(POFile, verbose_name=_('PO File'),
                               related_name='reviews',)
    author = models.ForeignKey(User)

    # Managers
    open_reviews = POReviewRequestManager()

    def __unicode__(self):
        return u"%(pofile)s %(id)s" % {
            'pofile': self.pofile,
            'id': self.id,
            }
