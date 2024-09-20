from django.db.models import Count, Q

from irhrs.core.constants.interviewer import PENDING, PROGRESS, COMPLETED
from irhrs.core.constants.payroll import REQUESTED, APPROVED, DENIED, CANCELED
from irhrs.hris.api.v1.serializers.exit_interview import ExitInterviewSerializer
from irhrs.hris.api.v1.serializers.resignation import UserResignationSerializer
from irhrs.hris.models import UserResignation
from irhrs.hris.models.exit_interview import ExitInterview


def exit_interview_queryset(user):
    return ExitInterview.objects.filter(interviewer=user).select_related(
        'separation', 'separation__employee', 'separation__employee__detail',
        'separation__employee__detail__job_title', 'interviewer', 'interviewer__detail',
        'interviewer__detail__job_title', 'question_set'
    )


def get_exit_interview_stats(user):
    return exit_interview_queryset(user).aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status=PENDING))
    )


def get_exit_interview(user):
    queryset = exit_interview_queryset(user)
    stats = queryset.aggregate(
        All=Count('id'),
        Pending=Count('id', filter=Q(status=PENDING)),
        Progress=Count('id', filter=Q(status=PROGRESS)),
        Completed=Count('id', filter=Q(status=COMPLETED)),
    )
    return queryset, stats, ExitInterviewSerializer


def resignation_queryset(user):
    return UserResignation.objects.filter(recipient=user).select_related(
        'employee', 'employee__detail', 'employee__detail__job_title',
        'employee__detail__organization', 'recipient', 'recipient__detail',
        'recipient__detail__job_title', 'recipient__detail__organization',
    )


def get_resignation_stats(user):
    return resignation_queryset(user).aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status=REQUESTED))
    )


def get_resignation(user):
    queryset = resignation_queryset(user)
    stats = queryset.aggregate(
        All=Count('id'),
        Requested=Count('id', filter=Q(status=REQUESTED)),
        Approved=Count('id', filter=Q(status=APPROVED)),
        Denied=Count('id', filter=Q(status=DENIED)),
        Canceled=Count('id', filter=Q(status=CANCELED)),
    )
    return queryset, stats, UserResignationSerializer
