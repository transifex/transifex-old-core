# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import get_model
from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_noop as _

Project = get_model('projects', 'Project')

register = template.Library()

@register.inclusion_tag('projects/hub_associate_project_toogler.html', takes_context=True)
def hub_associate_project_toogler(context, outsourced_project):
    """
    Handle watch links for objects by the logged in user
    """
    context['ENABLE_NOTICES'] = settings.ENABLE_NOTICES
    outsourced_project.url = reverse('hub_associate_project_toggler',
        args=(outsourced_project.outsource.slug,))
    context['outsourced_project'] = outsourced_project
    
    return context