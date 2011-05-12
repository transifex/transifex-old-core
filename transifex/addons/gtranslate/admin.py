# -*- coding: utf-8 -*-
from django.contrib import admin
from transifex.addons.gtranslate.models import Gtranslate

class GtranslateAdmin(admin.ModelAdmin):
    exclude = ('project', )

admin.site.register(Gtranslate, GtranslateAdmin)
