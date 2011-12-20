from django.contrib import admin
from transifex.projects.models import Project, HubRequest
from authority.admin import PermissionInline

class ProjectAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description']
    list_display = ['name', 'description']

admin.site.register(Project, ProjectAdmin, inlines=(PermissionInline,))
admin.site.register(HubRequest)

