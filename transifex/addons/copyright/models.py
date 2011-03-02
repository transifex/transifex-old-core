from django.db import models

from transifex.resources.models import RLStats as TranslatedResource

def get_copyright_text(user, resource, language):
    copyrights = Copyright.objects.filter(user=user,
                                          resource=resource,
                                          language=language)

class Copyright(models.Model):
    """A model holding copyrights.
    
    This should be representing a statement such as:
    # Copyright (C) 2014 John Doe.

    Multi-year copyright should happen using managers, resulting to:
    # Copyright (C) 2014-2015, 2018 John Doe.
    """

    # The copyright owner. We don't make this a foreign key, since
    # it might or might not be a user in our database.
    owner = models.CharField(_('Owner'), max_length=255,
        help_text=_("The copyright owner in text form."))

    # The copyright owner, in case the assignment is happening inside Tx.
    # No reason to use this -- only for backup purposes.
    user = models.ForeignKey(User, blank=False, null=False,
        verbose_name=_('User'),
        help_text=_("The Transifex user who owns the copyright, if applicable."))

    # The target translated resource object
    tresource = models.ForeignKey(RLStat,
        verbose_name=_('Translated Resource Object'),
        help_text=_("The Resource-Language object this copyright applies to."))

    year = models.DecimalField(_('Year of copyright'),
        blank=False, null=False, max_digits=4, decimal_places=0,
        help_text=_("The year of the copyright."))

    comment = models.CharField(_('Comment'),
        max_length=255, blank=False, null=False,
        help_text=_("A comment for this copyright."),)

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    def get_name(self):
        """Return the name for the copyright notice.
        
        self.owner should always be trusted. If for some reason it's not
        available, fallback to user info."""
        if self.owner:
            return self.owner
        else:
            if self.user.firstname

    def __unicode__(self):
        return u'Copyright (C) %(year)s %(owner)s' % {
            'year': self.year,
            'owner': self.owner or self.user}

    class Meta:
        unique_together = (('language', 'resource', 'owner', 'year'),)

