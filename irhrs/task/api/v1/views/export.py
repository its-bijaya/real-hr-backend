from django.conf import settings
from django.db.models import F
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView
from django.utils import timezone

from irhrs.core.utils.common import DummyObject
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.export.mixins.export import BackgroundTableExportMixin
from irhrs.hris.models import CoreTask
from irhrs.permission.constants.permissions import TASK_REPORT_PERMISSION
from irhrs.task.api.v1.permissions import TaskReportPermission
from irhrs.task.api.v1.serializers.task import TaskExportSerializer
from irhrs.task.constants import PENDING, IN_PROGRESS, COMPLETED, RESPONSIBLE_PERSON
from irhrs.task.models import Task

MEDIA_ROOT = settings.MEDIA_ROOT
BACKEND_URL = settings.BACKEND_URL


class TaskExport(BackgroundTableExportMixin, ListAPIView):
    permission_classes = [TaskReportPermission]
    notification_permissions = [TASK_REPORT_PERMISSION]
    export_type = "Task"
    serializer_class = TaskExportSerializer
    filter_backends = [FilterMapBackend, SearchFilter, OrderingFilter]

    search_fields = (
        "title",
        "description",
    )

    ordering_fields = (
        'id',
        'title',
        'deadline',
        'created_at'
    )

    filter_map = {
        'status': 'status',
        'priority': 'priority',
        'created_by': 'created_by',
        'approved': 'approved',
        'created_at': 'created_at',
        'start_date_from': 'created_at__date__gte',
        'start_date_to': 'created_at__date__lte',
        'finish_date_from': 'finish__date__gte',
        'finish_date_to': 'finish__date__lte'
    }

    def get_export_fields(self):
        export_fields = [
            {'name': 'id', 'title': 'Id'},
            {
                'name': 'created_by',
                'title': 'Created by',
                'fields': (
                    {'name': 'full_name', 'title': 'Name'},
                    {'name': 'employment_level', 'title': 'Level'},
                    {'name': 'organization', 'title': 'Organization'},
                    {'name': 'division', 'title': 'Division'}
                )
            },
            {
                'name': 'assigned_to',
                'title': 'Assigned to',
                'fields': (
                    {'name': 'full_name', 'title': 'Name'},
                    {'name': 'employment_level', 'title': 'Level'},
                    {'name': 'organization', 'title': 'Organization'},
                    {'name': 'division', 'title': 'Division'}
                )
            },
            {'name': 'created_at', 'title': 'Created at'},
            {'name': 'modified_at', 'title': 'Modified at'},
            {'name': 'project', 'title': 'Project'},
            {'name': 'title', 'title': 'Title'},
            {'name': 'deleted_at', 'title': 'Deleted at'},
            {'name': 'description', 'title': 'Description'},
            {'name': 'parent', 'title': 'Parent'},
            {'name': 'get_priority_display', 'title': 'Priority'},
            {'name': 'get_status_display', 'title': 'Status'},
            {'name': 'starts_at', 'title': 'Starts at'},
            {'name': 'deadline', 'title': 'Deadline'},
            {'name': 'start', 'title': 'Start'},
            {'name': 'finish', 'title': 'Finish'},
            {'name': 'changeable_deadline', 'title': 'Changeable deadline'},
            {'name': 'approve_required', 'title': 'Approve required'},
            {'name': 'approved', 'title': 'Approved'},
            {'name': 'approved_at', 'title': 'Approved at'},
            {'name': 'recurring_rule', 'title': 'Recurring rule'},
            {'name': 'recurring_first_run', 'title': 'Recurring first run'},
            {'name': 'freeze', 'title': 'Freeze'}
        ]

        return export_fields

    def get(self, request, **kwargs):
        return self._export_get()

    def post(self, request, **kwargs):
        return self._export_post()

    def get_queryset(self):
        return Task.objects.base().select_related(
            'created_by', 'created_by__detail', 'created_by__detail__employment_level',
            'created_by__detail__organization', 'created_by__detail__division'
        ).prefetch_related('task_associations', 'task_associations__user')

    def get_organization(self):
        return self.request.user.detail.organization

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        pre_condition = self.request.query_params.get("pre_condition")
        post_condition = self.request.query_params.get("post_condition")
        assignee = self.request.query_params.get("assignee")
        assigner = self.request.query_params.get("assigner")
        result_area = self.request.query_params.getlist("result_area")

        if pre_condition in ['pending', 'in_progress', 'completed']:
            if pre_condition == 'pending':
                queryset = queryset.filter(status=PENDING)
            elif pre_condition == 'in_progress':
                queryset = queryset.filter(status=IN_PROGRESS)
            elif pre_condition == 'completed':
                queryset = queryset.filter(status=COMPLETED)
        if post_condition in ['delayed', 'on_time']:
            if post_condition == 'delayed':
                if pre_condition == 'completed':
                    queryset = queryset.filter(deadline__lt=F('finish'))
                else:
                    queryset = queryset.filter(deadline__lte=timezone.now())
            elif post_condition == 'on_time':
                if pre_condition == 'completed':
                    queryset = queryset.filter(deadline__gt=F('finish'))
                else:
                    queryset = queryset.filter(deadline__gte=timezone.now())

        if assignee:
            queryset = queryset.filter(
                task_associations__user_id=int(assignee),
                task_associations__association=RESPONSIBLE_PERSON
            )
        if assigner:
            queryset = queryset.filter(created_by_id=int(assigner))

        if result_area:
            try:
                core_tasks = CoreTask.objects.filter(
                    result_area_id__in=result_area)
                queryset = queryset.filter(
                    task_associations__core_tasks__in=core_tasks)
            except (TypeError, ValueError):
                pass
        return queryset

    def get_extra_export_data(self):
        extra_data = super().get_extra_export_data()
        extra_data['serializer_context'] = {
            'request': DummyObject(
                method='GET',
                user=self.request.user
            )
        }
        extra_data['organization'] = self.request.user.detail.organization
        return extra_data

    def get_export_data(self):
        export_data = super().get_export_data()
        return export_data

    def get_frontend_redirect_url(self):
        return f'/admin/{self.request.user.detail.organization.slug}/task/reports/all-tasks'
