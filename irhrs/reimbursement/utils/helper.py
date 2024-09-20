import datetime
from functools import reduce

from django.conf import settings
from django.db.models import Count, Q

from irhrs.core.constants.payroll import APPROVED, DENIED, CANCELED, \
    SUPERVISOR, EMPLOYEE, REQUESTED
from irhrs.reimbursement.api.v1.serializers.reimbursement import AdvanceExpenseRequestSerializer, \
    AdvanceExpenseCancelHistorySerializer
from irhrs.reimbursement.api.v1.serializers.settlement import ExpenseSettlementSerializer
from irhrs.reimbursement.constants import TRAVEL, PER_DIEM, LODGING
from irhrs.reimbursement.models import AdvanceExpenseRequest, ExpenseSettlement
from irhrs.reimbursement.models.reimbursement import AdvanceExpenseCancelHistory
from irhrs.reimbursement.models.setting import ReimbursementSetting


def reimbursement_queryset(user, action):
    model_map = {
        'advance': AdvanceExpenseRequest,
        'settlement': ExpenseSettlement,
        'cancel': AdvanceExpenseCancelHistory
    }
    model = model_map.get(action)
    queryset = model.objects.filter(
        Q(recipient=user) |
        Q(
            Q(approvals__user=user),
            Q(approvals__role__in=[SUPERVISOR, EMPLOYEE]),
            Q(approvals__status__in=[APPROVED, DENIED])
        )
    )
    if action != 'cancel':
        return queryset.select_related(
            'employee', 'employee__detail', 'employee__detail__organization',
            'employee__detail__job_title',
        ).distinct()
    return queryset


def get_reimbursement_stats(user, action):
    return reimbursement_queryset(user, action).aggregate(
        total=Count('id', distinct=True),
        pending=Count('id', filter=Q(status=REQUESTED), distinct=True)
    )


def get_reimbursement(user, action):
    serializer_map = {
        'advance': AdvanceExpenseRequestSerializer,
        'settlement': ExpenseSettlementSerializer,
        'cancel': AdvanceExpenseCancelHistorySerializer
    }
    queryset = reimbursement_queryset(user, action)
    stats = queryset.aggregate(
        All=Count('id', distinct=True),
        Requested=Count('id', filter=Q(status=REQUESTED), distinct=True),
        Approved=Count('id', filter=Q(status=APPROVED), distinct=True),
        Denied=Count('id', filter=Q(status=DENIED), distinct=True),
        Canceled=Count('id', filter=Q(status=CANCELED), distinct=True),
    )
    return queryset, stats, serializer_map.get(action)


def calculate_total(details, expense_type):
    if not details:
        return 0
    if expense_type != TRAVEL:
        return reduce(
            lambda x, y: x + y,
            map(
                lambda detail: detail.get('rate') * detail.get('quantity'),
                details
            )
        )
    return reduce(
        lambda x, y: x + y,
        map(
            lambda detail: detail.get('day') * detail.get('rate_per_day'),
            details
        )
    )


def get_rate_per_type(detail_type, organization):
    per_diem_rate = settings.PER_DIEM_RATE
    lodging_rate = settings.LODGING_RATE
    other_rate = settings.OTHER_RATE

    reimbursement_setting = ReimbursementSetting.objects.filter(
       organization=organization
    ).first()
    if reimbursement_setting:
        per_diem_rate = reimbursement_setting.per_diem_rate
        lodging_rate = reimbursement_setting.lodging_rate
        other_rate = reimbursement_setting.others_rate

    detail_type_rate = {
        PER_DIEM: per_diem_rate,
        LODGING: lodging_rate
    }
    return detail_type_rate.get(detail_type, other_rate)


def calculate_advance_amount(details, expense_type, organization):
    if not details:
        return 0

    if expense_type == TRAVEL:
        return reduce(
            lambda x, y: x + y,
            map(
                lambda detail:
                detail.get('day') *
                detail.get('rate_per_day') *
                get_rate_per_type(
                    detail.get('detail_type'),
                    organization=organization
                ), details
            )
        )
    return calculate_total(details, expense_type)


def convert_to_iso_format(obj):
    if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
        return obj.isoformat()
    return obj
