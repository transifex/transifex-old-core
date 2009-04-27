from django.contrib import admin
from models import (Collection, CollectionRelease as Release)

admin.site.register(Collection)
admin.site.register(Release)