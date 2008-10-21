from django.contrib import admin
from translations.models import (Language, POFile)

admin.site.register(Language)
admin.site.register(POFile)