import django_filters
from actionlog.models import LogEntry

class LogEntryFilter(django_filters.FilterSet):
    action_time = django_filters.DateRangeFilter()
    class Meta:
        model = LogEntry
        fields = ['user', 'action_type', 'action_time']
