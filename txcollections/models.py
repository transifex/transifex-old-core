from markdown import markdown
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import permalink
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.utils.html import escape
import tagging
from tagging.fields import TagField

from releases.models import Release as ReleasesRelease

# The following is a tricky module, so we're including it only if needed
if settings.ENABLE_NOTICES:
    from notification import models as notification

class CollectionManager(models.Manager):
    pass


class Collection(models.Model):

    """A collection of projects (aka big-picture project)."""

    slug = models.SlugField(max_length=30,
        help_text=_('A short label to be used in the URL, containing only '
                    'letters, numbers, underscores or hyphens.'))
    name = models.CharField(max_length=50,
        help_text=_('A string like a name or very short description.'))
    description = models.CharField(blank=True, max_length=255,
        help_text=_('A sentence or two describing the object.'))
    long_description = models.TextField(blank=True, max_length=1000,
        help_text=_('A longer description (optional). Use Markdown syntax.'))
    homepage = models.URLField(blank=True, verify_exists=False)
    hidden = models.BooleanField(default=False,
        help_text=_('Hide this object from the list view?'))
    enabled = models.BooleanField(default=True,
        help_text=_('Enable this object or disable its use?'))
    created = models.DateField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    tags = TagField()
    
    # Normalized fields
    long_description_html = models.TextField(blank=True, max_length=1000,
         help_text=_('Description in HTML.'), editable=False)

    # Managers
    objects = CollectionManager()
        
    def __unicode__(self):
        return self.name

    def __repr__(self):
        return _('<Collection: %s>') % self.name
    
    class Meta:
        verbose_name = _('collection')
        verbose_name_plural = _('collections')
        db_table  = 'txcollections_collection'
        ordering  = ('name',)
        get_latest_by = 'created'

    @permalink
    def get_absolute_url(self):
        return ('collection_detail', None,
                { 'slug': self.slug, })

    def save(self, *args, **kwargs):
        desc_escaped = escape(self.long_description)
        self.long_description_html = markdown(desc_escaped)
        created = self.created
        super(Collection, self).save(*args, **kwargs)

        if not created and settings.ENABLE_NOTICES:
            notification.send(User.objects.all(), "collections_new_collection",
                              {'collection': self})

tagging.register(Collection, tag_descriptor_attr='tagsobj')


# Releases

class ReleaseManager(models.Manager):
    pass


class CollectionRelease(ReleasesRelease):

    """
    A collection of packages shipped in a Collection (eg. Fedora 9).
    
    Represents a packaging and releasing of a software project (big or
    small) on a particular date, for which makes sense to track
    translations across the whole release.
        
    Inherits from the generic release.Release.
    """
    
    # Relations
    
    collection = models.ForeignKey(Collection, related_name='releases')
    
    def __unicode__(self):
        return self.name

    @property
    def full_name(self):
        return "%s: %s" % (self.collection.name, self.name)

    def __repr__(self):
        return _('<Release: %(rel)s (Collection %(col)s)>') % {
            'rel': self.name,
            'col': self.collection.name}
    
    class Meta(ReleasesRelease.Meta):
        """Inherits from the parent object's Meta class."""
        db_table  = 'collections_release'
        unique_together = ['slug', 'collection']

    @permalink
    def get_absolute_url(self):
        return ('collection_release_detail', None,
                { 'slug': self.collection.slug, 'release_slug': self.slug})

tagging.register(CollectionRelease, tag_descriptor_attr='tagsobj')
