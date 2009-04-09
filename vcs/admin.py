from django.contrib import admin
from vcs.models import VcsUnit

class VcsUnitAdmin(admin.ModelAdmin):
    pass

admin.site.register(VcsUnit, VcsUnitAdmin)
