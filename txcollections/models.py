from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import permalink
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
import tagging
from tagging.fields import TagField


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
        help_text=_('Use Markdown syntax.'))
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
        import markdown
        from cgi import escape
        desc_escaped = escape(self.long_description)
        self.long_description_html = markdown.markdown(desc_escaped)
        created = self.created
        super(Collection, self).save(*args, **kwargs)

        if not created and settings.ENABLE_NOTICES:
            notification.send(User.objects.all(), "collections_new_collection",
                              {'collection': self})

tagging.register(Collection, tag_descriptor_attr='tagsobj')
