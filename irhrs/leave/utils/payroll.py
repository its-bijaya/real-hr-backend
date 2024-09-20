"""@irhrs_docs"""
import typing
from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Sum, fields as dj_fields, Count, Q, OuterRef, Subquery, Exists, F, Case, When

from django.db.models.functions import Coalesce

from irhrs.attendance.constants import HOLIDAY, WORKDAY, NO_LEAVE, CREDIT_HOUR as CREDIT_HOUR_ATTENDANCE
from irhrs.attendance.models import TimeSheet
from irhrs.leave.constants.model_constants import APPROVED, REQUESTED, FORWARDED, CREDIT_HOUR, \
    TIME_OFF
from irhrs.leave.models import LeaveAccount, LeaveAccountHistory
from irhrs.leave.models.account import LeaveEncashment
from irhrs.leave.models.request import LeaveSheet, LeaveRequest, HourlyLeavePerDay

USER = get_user_model()

HOURLY_LEAVES = (CREDIT_HOUR, TIME_OFF)


def get_leave_days_from_hourly(user: USER,
                               start: date,
                               end: date,
                               is_paid: bool = None,
                               is_workday: bool = None):
    fil = {
    }
    annotates = {}

    if is_paid is not None:
        fil['is_paid'] = is_paid

    if is_workday is not None:
        annotates['is_workday'] = Exists(
                TimeSheet.objects.filter(
                    timesheet_user=OuterRef('user'),
                    timesheet_for=OuterRef('leave_for'),
                    coefficient=WORKDAY
                )
            )
        fil['is_workday'] = is_workday

    return HourlyLeavePerDay.objects.filter(
        user=user, leave_for__range=(start, end)
    ).annotate(**annotates).filter(**fil).aggregate(
        sum=Coalesce(
            Sum('balance', output_field=dj_fields.FloatField()), 0.0)
    ).get('sum')


def get_leave_days(
    user: USER, start: date, end: date,
    is_paid: bool = None,
    is_workday: bool = None
):
    fil = {}
    annotates = {}

    if is_paid is not None:
        fil.update({'request__leave_rule__is_paid': is_paid})

    if is_workday is not None:
        annotates.update({
            'is_workday': Exists(
                TimeSheet.objects.filter(
                    timesheet_user=OuterRef('request__user'),
                    timesheet_for=OuterRef('leave_for'),
                    coefficient=WORKDAY)
            )
        })
        fil.update({'is_workday': is_workday})

    daily_leaves = LeaveSheet.objects.filter(
        request__status=APPROVED,
        request__is_deleted=False,
        request__user=user
    ).filter(
        ~Q(request__leave_rule__leave_type__category__in=HOURLY_LEAVES)
    ).filter(
        leave_for__range=[start, end]
    ).annotate(**annotates).filter(**fil).aggregate(
        sum=Coalesce(
            Sum('balance', output_field=dj_fields.FloatField()), 0.0)
    ).get('sum')

    hourly_leaves = get_leave_days_from_hourly(user, start, end, is_paid, is_workday)

    return daily_leaves + hourly_leaves


def get_all_leave_days(user: USER, start: date, end: date):
    """
    Get all leave days of a user for given date range
    :returns: total_leave_days
    """
    return get_leave_days(user, start, end)


def get_unpaid_leave_days(user: USER, start: date, end: date, is_workday: bool = None):
    """
    Get unpaid leave days for given user for given date range
    :returns It is a float value. 0.5 for half day leave.
    """
    return get_leave_days(user, start, end, is_paid=False, is_workday=is_workday)


def get_paid_leave_days(user: USER, start: date, end: date, is_workday: bool = None):
    """
    Get paid leave days for given user for given date range
    :returns It is a float value. 0.5 for half day leave.
    """
    return get_leave_days(user, start, end, is_paid=True, is_workday=is_workday)


def get_users_by_status(status, user_filter):
    from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
    return UserThinSerializer(
        USER.objects.filter(
            leave_requests__status=status, **user_filter
        ).distinct('id'),
        fields=('id', 'full_name', 'profile_picture', 'job_title', 'organization', 'is_current', 'is_online'),
        many=True).data


def get_leave_request_status_summary(
        organization_slug: str, start: date,
        end: date, user_filter: dict,
        exclude_filter: typing.Union[dict, None] = None
) -> dict:
    """
    Leave Request Status Summary
    ---------------------------------

    Leave request status summary for given filters

    :param organization_slug: organization slug of user
    :param start: start of range for timesheet_for
    :param end: end of range for timesheet_for
    :param user_filter: dictionary of filters to be applied on USER model
    :param exclude_filter: dictionary of filters to be excluded on USER model
    :return: counts of leave request status pending, forwarded, approved
    """

    fil = dict(detail__organization__slug=organization_slug)
    fil.update(user_filter)

    leave_filter = {f"user__{key}": value for key, value in fil.items()}
    leave_filter.update({
        'start__date__gte': start,
        'end__date__lte': end
    })
    qs = LeaveRequest.objects.filter(**leave_filter)
    if exclude_filter:
        qs = qs.exclude(**exclude_filter)

    stat = qs.aggregate(
        pending=Count('id', filter=Q(status=REQUESTED), distinct=True),
        forwarded=Count('id', filter=Q(status=FORWARDED), distinct=True),
        approved=Count('id', filter=Q(status=APPROVED), distinct=True),
    )

    user_fil = {}
    user_fil['detail__organization__slug'] = organization_slug
    user_fil['leave_requests__start__date__gte'] = start
    user_fil['leave_requests__end__date__lte'] = end
    user_fil['leave_requests__is_deleted'] = False

    user_ids = user_filter.get('id__in')

    if user_ids:
        user_fil['leave_requests__user_id__in'] = user_ids
        
    return {
        "pending_users": get_users_by_status(REQUESTED, user_fil),
        "forwarded_users": get_users_by_status(FORWARDED, user_fil),
        "approved_users": get_users_by_status(APPROVED, user_fil),
        **stat}


def get_leave_balance_report(user: USER, start: date, end: date):
    """
    Leave balance reports for given range
    :returns QuerySet annotated with.
    """

    opening_balance_query = LeaveAccountHistory.objects.filter(
        account_id=OuterRef('pk'),
        created_at__date__lte=start
    ).order_by('-created_at').values('new_usable_balance')[:1]

    closing_balance_query = LeaveAccountHistory.objects.filter(
        account_id=OuterRef('pk'),
        created_at__date__lte=end
    ).order_by('-created_at').values('new_usable_balance')[:1]

    used_balance = LeaveSheet.objects.filter(
        leave_for__range=(start, end),
        request__leave_account_id=OuterRef('pk'),
        request__status=APPROVED,
        request__is_deleted=False,
    ).order_by().values('request__leave_account_id').annotate(
        consumed=Sum(
            Case(
                When(
                    request__leave_rule__leave_type__category=CREDIT_HOUR,
                    then=F('request__balance')
                ),
                default=F('balance')
            )
        )
    ).values('consumed')[:1]

    return LeaveAccount.objects.filter(user=user).select_related(
        'rule',
        'rule__leave_type',
    ).annotate(
        opening=Coalesce(Subquery(opening_balance_query, output_field=dj_fields.FloatField(default=0)), 0.0),
        used=Coalesce(Subquery(used_balance, output_field=dj_fields.FloatField(default=0)), 0.0),
        closing=Coalesce(Subquery(closing_balance_query, output_field=dj_fields.FloatField(default=0)), 0.0)
    )


def encashment_count(user, start_date, end_date, divide=False):
    """
    Returns the total encashed balance for a user in a given interval from all
    accounts, aggregated
    Send a flag for trails to divide between the leave accounts.
    :param user: User object
    :param start_date: Start of payroll calculation date
    :param end_date: End of payroll calculation date
    :param divide: True sends a list of division, False sends total.
    :return: Total encashment balance count.
    """
    # leave encashment is created at the time of renewal only.
    # It is safe to assume that the leave renewal and encashment creation is at
    # almost same time
    qs = LeaveEncashment.objects.filter(
        account__user=user,
        created_at__date__range=(start_date, end_date)
    )
    total_encashed = qs.aggregate(
        total_encashed=Sum('balance')
    ).get(
        'total_encashed'
    )
    if not divide:
        return total_encashed
    return_dict = qs.order_by().values(
        'account__rule__leave_type__name'
    ).annotate(
        total_encashed=Sum(
            'balance'
        )
    ).values_list(
        'account__rule__leave_type__name',
        'total_encashed'
    )
    return [
        dict(
            zip(
                ('leave_type', 'total_encashed'),
                val
            )
        ) for val in return_dict
    ], total_encashed


def get_half_credit_leave_sum(user, start, end, is_present=True):
    equivalent_time_sheet = TimeSheet.objects.filter(
        timesheet_user=user,
        timesheet_for=OuterRef('leave_for'),
        hour_off_coefficient=CREDIT_HOUR_ATTENDANCE,
        is_present=is_present,
    )
    leave_sheet_for_the_day = LeaveSheet.objects.filter(
        balance=0.5,
        request__status=APPROVED,
        request__is_deleted=False,
        leave_for__range=(start, end),
        request__leave_rule__leave_type__category=CREDIT_HOUR,
        request__user=user
    ).annotate(
        was_present_for_the_day=Exists(equivalent_time_sheet)
    ).filter(
        was_present_for_the_day=True
    ).aggregate(
        total_sum=Sum('balance')
    ).get('total_sum') or 0
    return leave_sheet_for_the_day
