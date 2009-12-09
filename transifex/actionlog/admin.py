from django.contrib import admin
from actionlog.models import LogEntry

class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'message', 'content_type', 'object_id', 'user')

admin.site.register(LogEntry, LogEntryAdmin)