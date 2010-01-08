from django.contrib import admin
from reviews.models import POReviewRequest
from translations.models import POFile

class POReviewRequestAdmin(admin.ModelAdmin):
    list_display = [f.name for f in POReviewRequest._meta.fields]

admin.site.register(POReviewRequest, POReviewRequestAdmin)

