from django.contrib import admin
from actionlog.models import LogEntry

class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'message_safe', 'user', 'action_time')
    search_fields = ['action_type__label', 'message']

admin.site.register(LogEntry, LogEntryAdmin)