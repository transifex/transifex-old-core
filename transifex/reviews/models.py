"""
This module contains a model representation
of the review request. The following definitions are used:

POReviewRequest: A file under review entry in the database.
"""

from django.db import models
from django.contrib.auth.models import User
from transifex.tralnslations.models import POFile

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

    # Core fields
    pofile = models.ForeignKey(POFile)
    author = models.ForeignKey(User)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='O')
    resolution = models.CharField(max_length=1, choices=RESOLUTION_CHOICES, default='N')    
    created_on = models.DateTimeField(auto_now_add=True, 
        help_text="Date and time of creation")
    last_updated = models.DateTimeField(auto_add=True, 
        help_text="Date and time of last update")

    def __unicode__(self):
        return u"%(pofile)s %(id)s" % {
            'pofile': self.pofile,
            'id': self.id,
            }