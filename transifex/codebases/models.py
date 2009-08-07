"""
This module contains a model that is expected to be used for the
codebases used by Transifex. The following definitions are used:

resource:
  A file within a codebase
codebase:
  A collection of files (VCS repo, tarball, etc.) that contains
  resources, some or all of which are to be translated
"""
import operator

from django.db import models
from django.utils.translation import ugettext_lazy as _

import settings
from codebases import need_browser
from txcommon.log import log_model
from txcommon.models import inclusive_fields

UNIT_CHOICES = settings.CODEBASE_CHOICES.items()
UNIT_CHOICES.sort(key=operator.itemgetter(0))

class Unit(models.Model):
    """
    An abstract codebase; a VCS repo, tarball, or some other piece of
    code.

    The following methods should be implemented by children:
      prepare
      teardown
      get_files
      get_rev
      submit
    """
    name = models.CharField(_('Name'), unique=True, max_length=100)
    root = models.CharField(_('Root'), max_length=255,
        help_text=_("The URL of the codebase"))
    type = models.CharField(_('Type'), max_length=10,
        choices=UNIT_CHOICES,
        help_text=_('The codebase type (%s)' %
                    ', '.join(settings.CODEBASE_CHOICES)))
    last_checkout = models.DateTimeField(null=True, editable=False,
        help_text=_("The last time this unit was updated"))

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __repr__(self):
        return '<Unit: %(name)s)>' % {'name': self.name}

    class Meta:
        verbose_name = _('unit')
        verbose_name_plural = _('units')
        ordering  = ('name',)
        get_latest_by = 'created'

    def prepare(self):
        """
        Prepares the codebase for use by Transifex by downloading,
        extracting, etc.
        """
        raise NotImplementedError()

    def teardown(self):
        """
        Cleans out any downloads used by the codebase
        """
        raise NotImplementedError()

    def get_files(self, filter):
        """
        Returns one or more resources within to the codebase as given
        by the filter
        """
        raise NotImplementedError()

    def get_rev(self, path):
        """
        Returns the current revision of either the codebase or of a
        resource within it
        """
        raise NotImplementedError()

    def submit(self, files, message, user):
        """
        Replaces one or more of the resources in a codebase with
        supplied contents
        """
        raise NotImplementedError()

    def promote(self):
        '''
        Returns a descendent model that refers to this codebase
        '''
        for cls in Unit.__subclasses__():
            if self.type in cls.unit_types:
                return cls.bootstrap(self)
        else:
            raise ValueError('Unknown unit type %r' % self.type)

    @classmethod
    def bootstrap(cls, unit):
        '''
        Creates a descendent from a Unit and returns it, saving if a
        new Unit descendant is created
        '''
        try:
            newunit = cls.objects.get(pk=unit.pk)
        except cls.DoesNotExist:
            newunit = cls()
            newunit.pk = unit.pk
            cls.bootstrap_extra(newunit)
            for field in inclusive_fields(type(unit)):
                setattr(newunit, field.name, getattr(unit, field.name))
            newunit.save()
        return newunit

    @classmethod
    def bootstrap_extra(cls, unit):
        '''
        Extra initialization after bootstrapping
        Descendents should override as necessary
        '''
        pass

log_model(Unit)
