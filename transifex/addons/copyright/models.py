from datetime import date
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from transifex.resources.models import RLStats as TranslatedResource

class CopyrightManager(models.Manager):
    def assign(self, tresource, owner, year=date.today().year):
        """Add copyright for a specific year to an object.
        
        If there is no copyright object, create. Otherwise, update if
        necessary.
        
        Should be called from Copyright.objects. Calling it from related models
        won't work.
        """ 
        #FIXME: Make this work with foreign-key calls, for example:
        #       tresource.objects.assign(owner=, year=)
        _qs = super(CopyrightManager, self).get_query_set()
        copyright, created = _qs.get_or_create(owner=owner, tresource=tresource,
                                               defaults={'years': year})
        if not created:
            # Copyright exists, let's update it
            years = copyright.years.split(',')
            if not year in years:
                years.append(year)
                copyright.years = ','.join(sorted(years))
                copyright.save()
        return copyright


class Copyright(models.Model):
    """A model holding copyrights.
    
    This should be representing a statement such as:
    # Copyright (C) 2014, 2015, 2018 John Doe.

    Years are stored in a CommaSeparatedIntegerField.
    """

    # The copyright owner. We don't make this a foreign key, since
    # it might or might not be a user in our database.
    owner = models.CharField(_('Owner'), max_length=255,
        help_text=_("The copyright owner in text form."))

    # The copyright owner, in case the assignment is happening inside Tx.
    # No reason to use this -- only for backup purposes.
    user = models.ForeignKey(User, blank=True, null=True,
        related_name='copyrights',
        verbose_name=_('User'),
        help_text=_("The Transifex user who owns the copyright, if applicable."))

    # The target translated resource object
    tresource = models.ForeignKey(TranslatedResource,
        blank=True, null=True,
        related_name='copyrights',
        verbose_name=_('Translated Resource Object'),
        help_text=_("The Resource-Language object this copyright applies to."))

    years = models.CommaSeparatedIntegerField(_('Years of copyright'),
        max_length=50,
        help_text=_("The years of the copyright."))

    comment = models.CharField(_('Comment'),
        max_length=255,
        help_text=_("A comment for this copyright."),)

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = (('tresource', 'owner'),)

    def __unicode__(self):
        return u'%(years)s %(owner)s' % {
            'years': self.years,
            'owner': self.owner or self.user}

    def __str__(self):
        return u'Copyright (C) %(years)s %(owner)s.' % {
            'years': str(self.years),
            'owner': self.owner or self.user}

    objects = CopyrightManager()

