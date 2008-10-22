from django.db import models


class Hold(models.Model):
    
    """A hold on something."""

    description = models.CharField(max_length=255)
    long_description = models.TextField(null=True, max_length=1000,
        help_text='Use Markdown syntax.')

    enabled = models.BooleanField(default=True,
        help_text=_('Enable this object or disable its use?'))
    created = models.DateField(auto_now_add=True, editable=False)
    modified = models.DateField(auto_now=True, editable=False)

    # Normalized fields
    long_description_html = models.TextField(blank=True, max_length=1000, 
        help_text=_('Description in HTML.'), editable=False)

    # TODO: Add generic relation details...