from django.contrib import admin
from projects.models import Project, Component


class ProjectAdmin(admin.ModelAdmin):
    #FIXME
    #prepopulated_fields = {'slug': ('name',)}
    pass

class ComponentAdmin(admin.ModelAdmin):
    #FIXME
    #prepopulated_fields = {'slug': ('name',)}
    pass

admin.site.register(Project, ProjectAdmin)
admin.site.register(Component, ComponentAdmin)