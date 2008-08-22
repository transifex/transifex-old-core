from django import template
from django.conf import settings
from django.db import models

register = template.Library()

#Project = models.get_model('projects', 'Project')


class EditProjectNode(template.Node):
    from django.conf.urls.defaults import url

    def __init__(self):
        pass
    def render(self, context):
        return (''
'<a href="/projects/edit/"><img border=0 src="{{MEDIA_URL}}/images/icons/pencil.png" /></a>'
'<a href="/projects/delete/"><img border=0 src="{{MEDIA_URL}}/images/icons/cross.png" /></a>')


@register.tag
def editproject_icon(parser, token):
    return EditProjectNode()
