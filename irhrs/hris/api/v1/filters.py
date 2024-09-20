from django.db.models import Q
from django_filters.rest_framework import filters, FilterSet

from irhrs.event.models import Event


class EventFilterSet(FilterSet):
    start_date = filters.DateFilter(
        method='filter_start_date'
    )
    end_date = filters.DateFilter(
        method='filter_end_date'
    )

    def filter_end_date(self, queryset, name, value):
        qs = queryset.filter(start_at__date__lte=value)
        return qs

    def filter_start_date(self, queryset, name, value):
        # also include events whose end date is
        # after start_date query param
        qs = queryset.filter(
            Q(
                Q(start_at__gte=value) |
                Q(end_at__gte=value)
            )
        )
        return qs

    class Meta:
        model = Event
        fields = ('start_date', 'end_date')
