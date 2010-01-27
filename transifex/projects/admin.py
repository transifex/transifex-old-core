from django.contrib import admin
from projects.models import *
from authority.admin import PermissionInline

admin.site.register(Project, inlines=(PermissionInline,))
admin.site.register(Component)
admin.site.register(Release)
