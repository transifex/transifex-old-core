"""
This module contains a model that is expected to be used for the
codebases used by Transifex. The following definitions are used:

resource: A file within a codebase
codebase: A collection of files (VCS repo, tarball, etc.) that contains
  resources, some or all of which are to be translated
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

import settings

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
    name = models.CharField(unique=True, max_length=100)
    root = models.CharField(max_length=255,
        help_text=_("The URL of the codebase"))
    type = models.CharField(max_length=10,
        choices=settings.CODEBASE_CHOICES.items(),
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
