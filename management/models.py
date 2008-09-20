from django.db import models
from projects.models import Project

class Hold(models.Model):
    """ A hold on a project """
    description = models.CharField(max_length=255)
    long_description = models.TextField(null=True, max_length=1000,
        help_text='Use Markdown syntax.')
    long_description_html = models.TextField(blank=True, null=True)

#    directors     = models.ManyToManyField(Person, limit_choices_to={'person_types__slug__exact': 'director'}, blank=True)
    project        = models.ForeignKey(Project)

    enabled = models.BooleanField(default=True)
    created = models.DateField(blank=True, null=True, editable=False)
