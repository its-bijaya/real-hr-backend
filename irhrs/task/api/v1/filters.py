from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from irhrs.task.models import Task

CYCLE_STATUS_MAPS = (
    ('Score Not Provided','Score Not Provided'),
    ('Forwarded To HR','Forwarded To HR'),
    ('Approved By HR','Approved By HR'),
    ('Acknowledged','Acknowledged'),
    ('Not Acknowledged','Not Acknowledged'),
    ('Acknowledge Pending','Acknowledge Pending'),
    ('Approval Pending','Approval Pending')
)


class TaskScoresAndCycleFilterSet(filters.FilterSet):
    creator = filters.ModelChoiceFilter(
        field_name='created_by',
        queryset=get_user_model().objects.all().current()
    )
    responsible = filters.ModelChoiceFilter(
        field_name='task_associations__user',
        queryset=get_user_model().objects.all().current()
    )

    class Meta:
        model = Task
        fields = ('creator', 'responsible',)
