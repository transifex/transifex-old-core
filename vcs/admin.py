from django.contrib import admin
from vcs.models import Unit

class UnitAdmin(admin.ModelAdmin):
    #FIXME
    #prepopulated_fields = {'slug': ('name',)}
    pass

admin.site.register(Unit, UnitAdmin)