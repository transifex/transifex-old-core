from django.contrib import admin
from vcs.models import Repository, Unit


class RepositoryAdmin(admin.ModelAdmin):
    #FIXME
    #prepopulated_fields = {'slug': ('name',)}
    pass

class UnitAdmin(admin.ModelAdmin):
    #FIXME
    #prepopulated_fields = {'slug': ('name',)}
    pass

admin.site.register(Repository, RepositoryAdmin)
admin.site.register(Unit, UnitAdmin)