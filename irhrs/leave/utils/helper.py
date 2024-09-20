from django.db.models import Count, Q

from irhrs.leave.api.v1.serializers.leave_request import LeaveRequestSerializer
from irhrs.leave.constants.model_constants import APPROVED, DENIED, FORWARDED, APPROVER
from irhrs.leave.models import LeaveRequest


def leave_request_queryset(user):
    return LeaveRequest.objects.filter(
        recipient=user,
        recipient_type=APPROVER
    ).select_related(
        'user', 'user__detail', 'user__detail__organization',
        'user__detail__division', 'user__detail__branch',
        'user__detail__employment_status', 'user__detail__employment_level',
        'user__detail__job_title', 'created_by', 'created_by__detail',
        'created_by__detail__organization', 'created_by__detail__division',
        'created_by__detail__branch', 'created_by__detail__employment_status',
        'created_by__detail__employment_level', 'created_by__detail__job_title',
        'leave_account', 'leave_account__rule__leave_type'
    )


def get_leave_request_stats(user):
    return leave_request_queryset(user).aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status=FORWARDED))
    )


def get_leave_request(user):
    queryset = leave_request_queryset(user)
    stats = queryset.aggregate(
        All=Count('id'),
        Forwarded=Count('id', filter=Q(status=FORWARDED)),
        Approved=Count('id', filter=Q(status=APPROVED)),
        Denied=Count('id', filter=Q(status=DENIED)),
    )
    return queryset, stats, LeaveRequestSerializer
