from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import permalink
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic

# The following is a tricky module, so we're including it only if needed
if settings.ENABLE_NOTICES:
    from notification import models as notification


class Release(models.Model):

    """
    A collection of packages of actual files, shipped together (eg. Fedora 9).
    
    Represents a packaging and releasing of a software project (big or
    small) on a particular date, for which makes sense to track
    translations across the whole release.
    
    Examples of Releases is GNOME 2.26, Fedora 10, PackageKit 0.3 etc.
    """

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

    release_date = models.DateTimeField(blank=True, null=True,
        help_text=_('When this release will be available.'))
    stringfreeze_date = models.DateTimeField(blank=True, null=True,
        help_text=_("When the translatable strings will be frozen (no strings "
                    "can be added/modified which affect translations."))
    develfreeze_date = models.DateTimeField(blank=True, null=True,
        help_text=_("The last date packages from this release can be built "
                    "from the developers, and thus, translations to be "
                    "built in the packages of it."))
    
    hidden = models.BooleanField(default=False,
        help_text=_('Hide this object from the list view?'))
    enabled = models.BooleanField(default=True,
        help_text=_('Enable this object or disable its use?'))
    created = models.DateField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    
    # Normalized fields
    long_description_html = models.TextField(blank=True, max_length=1000,
         help_text=_('Description in HTML.'), editable=False)

    class Meta:
        abstract = True
        verbose_name = _('release')
        verbose_name_plural = _('releases')
        ordering  = ('name',)
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        import markdown
        from cgi import escape
        desc_escaped = escape(self.long_description)
        self.long_description_html = markdown.markdown(desc_escaped)
        created = self.created
        super(Release, self).save(*args, **kwargs)

        if not created and settings.ENABLE_NOTICES:
            notification.send(User.objects.all(), "releases_new_release",
                              {'release': self})
