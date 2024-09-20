"""@irhrs_docs"""
import datetime
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum, Exists, OuterRef, F, Case, When, PositiveSmallIntegerField
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from irhrs.attendance.constants import UNCLAIMED, DECLINED, WORKDAY, OFFDAY, HOLIDAY
from irhrs.attendance.models import OvertimeClaim
from irhrs.core.utils import nested_getattr, get_system_admin
from irhrs.core.utils.common import get_today, relative_delta_gte, combine_aware, \
    humanize_interval, DummyObject
from irhrs.core.utils.dependency import get_dependency
from irhrs.leave.constants.model_constants import (
    APPROVED, DENIED, YEARS, MONTHS, DAYS,
    REQUESTED, FORWARDED, FIRST_HALF, SECOND_HALF,
    SUPERVISOR, APPROVER, TIME_OFF, CREDIT_HOUR,
    HOURS, MINUTES, FULL_DAY, INCLUDE_HOLIDAY, INCLUDE_HOLIDAY_AND_OFF_DAY,
    INCLUDE_OFF_DAY)
from irhrs.leave.models.account import AdjacentTimeSheetOffdayHolidayPenalty
from irhrs.leave.models.request import LeaveSheet, LeaveRequest
from irhrs.leave.models.settings import LeaveApproval
from irhrs.notification.utils import notify_organization
from irhrs.permission.constants.permissions import LEAVE_PERMISSION, LEAVE_REQUEST_PERMISSION
from irhrs.users.models import UserSupervisor

User = get_user_model()
ADJACENT_HOLIDAY_OFFDAY_INCLUSION_DAYS = settings.ADJACENT_HOLIDAY_OFFDAY_INCLUSION_DAYS


def get_appropriate_recipient(user, level=1, has_approvals=False):
    """
    Returns recipient as
    :param user:
    :param level:
    :param has_approvals:
    :return:
    """
    if has_approvals:
        return getattr(
            LeaveApproval.objects.filter(
                organization=user.detail.organization,
                authority_order=level
            ).first(),
            'employee',
            None
        )
    return getattr(
        user.supervisors.filter(authority_order=level).first(),
        'supervisor',
        None
    )


def get_authority(user, recipient, has_approvals=False, recipient_type=SUPERVISOR):
    if not has_approvals:
        obj = user.supervisors.filter(supervisor=recipient).first()
    else:
        if recipient_type == SUPERVISOR:
            obj = None
        else:
            obj = LeaveApproval.objects.filter(
                organization=user.detail.organization,
                employee=recipient
            ).first()
    return obj.authority_order if obj else None


def get_on_leave_employees(date, filters=None):
    filters = filters or {}
    filters.update({
        'leave_sheet_exists': True
    })
    return User.objects.annotate(
        leave_sheet_exists=Exists(
            LeaveSheet.objects.filter(
                leave_for=date,
                request__status=APPROVED,
                request__is_deleted=False
            ).filter(
                request__user_id=OuterRef('id')
            )
        )
    ).filter(**filters).distinct()


def validate_can_request_assign(leave_account, user, mode=""):
    """
    Validate if user can request this leave

    checks employee_can_apply and admin_can_assign rules
    """
    employee_can_apply = leave_account.rule.employee_can_apply
    admin_can_assign = leave_account.rule.admin_can_assign

    if employee_can_apply and leave_account.user == user:
        return
    if mode == "hr" and admin_can_assign and LEAVE_PERMISSION.get(
        'code'
    ) in user.get_hrs_permissions(leave_account.user.detail.organization):
        return
    if user == get_system_admin():
        return
    raise ValidationError(
        "You cannot request this leave."
    )


def check_multi_level_approval(rule):
    return nested_getattr(rule, 'leave_type.multi_level_approval')


def get_recipient(user, recipient, status, recipient_type, has_approvals=False):
    current_level = get_authority(user, recipient, has_approvals, recipient_type) or 0
    recipient_map = {
        REQUESTED: get_appropriate_recipient(user, level=1),
        FORWARDED: get_appropriate_recipient(user, current_level + 1),
        APPROVED: get_appropriate_recipient(
            user=user,
            level=current_level + 1,
            has_approvals=has_approvals
        ) if has_approvals else recipient,
        DENIED: recipient
    }
    rec = recipient_map.get(status)

    if has_approvals and status == APPROVED:
        recipient_type = APPROVER
        status = FORWARDED
        if not rec:
            # it is used to check after supervisor approval whether there
            # are any employee on approval levels or not
            status = APPROVED
            rec = recipient
            if recipient_type == SUPERVISOR:
                recipient_type = SUPERVISOR

    if isinstance(rec, UserSupervisor):
        return getattr(rec, 'supervisor'), recipient_type, status

    return (rec or get_system_admin()), recipient_type, status


def get_leave_request_recipient(leave_request):
    has_approvals = False
    status = leave_request.status
    recipient_type = leave_request.recipient_type

    if status == APPROVED:
        has_approvals = True if recipient_type == APPROVER else \
            check_multi_level_approval(leave_request.leave_rule)

    return get_recipient(
        user=leave_request.user,
        recipient=leave_request.recipient,
        status=status,
        recipient_type=recipient_type,
        has_approvals=has_approvals
    )


def validate_has_supervisor(status, user, recipient=None):
    # user whose first level supervisor is to be tested for
    if status == REQUESTED:
        # The supervisor isn't taken from user.first_level_supervisor due to implementation changes.
        # sup = getattr(user, 'first_level_supervisor', None)
        sup = UserSupervisor.objects.filter(
            user=user,
            authority_order=1
        ).first()
        if sup:
            return sup
    elif status == FORWARDED:
        authority = get_authority(user, recipient)
        if authority:
            sup = get_appropriate_recipient(user, authority + 1)
            if sup:
                return sup
    elif status in [DENIED, APPROVED]:
        return
    raise ValidationError(
        'Cannot act on this request because no supervisor is assigned for '
        'this action.'
    )


def validate_holiday_inclusive(leave_account, start, end):
    """
    Holiday Inclusive test is useful for start and end dates only.
    """
    return
    # is_holiday_inclusive = leave_account.rule.holiday_inclusive
    # if is_holiday_inclusive:
    #     return
    # user = leave_account.user
    # errors = dict()
    # if user.is_holiday(start):
    #     errors['start'] = f'The start date {start} is a holiday.'
    # if start != end and user.is_holiday(end):
    #     errors['end'] = f'The end date {end} is a holiday.'
    # if errors:
    #     raise ValidationError(errors)


def validate_leave_occurrence(leave_account, start):
    """
    Validates the number of leave requests.
    :param leave_account: Leave Account
    :param start: start datetime of leave
    :return:
    """

    # if occurrence policy is disabled in master settings
    if not leave_account.master_setting.occurrences:
        return

    leave_limit = leave_account.rule.limit_leave_occurrence
    duration = leave_account.rule.limit_leave_occurrence_duration
    duration_type = leave_account.rule.limit_leave_occurrence_duration_type

    # if values are zero or incomplete ignore
    if leave_limit == 0 or duration == 0 or not duration_type:
        return

    blame = {
        YEARS: relativedelta(years=duration),
        MONTHS: relativedelta(months=duration)
    }.get(duration_type)
    duration_type_str = duration_type.replace('s', '(s)')

    if leave_account.leave_requests.exclude(status=DENIED).filter(
        start__gte=start.date() - blame
    ).count() >= leave_limit:
        raise ValidationError(
            "The maximum leave request limit has exceeded. The maximum leave "
            f"requests allowed in {duration} {duration_type_str} duration "
            f"is {leave_limit}."
        )


def validate_depletion_required(leave_account):
    """
    Validates if the leave can be applied only if other leaves are exhausted.
    :return:
    """

    # if depletion policy is disabled in master settings ignore
    if not leave_account.master_setting.depletion_required:
        return

    depletion_leave_types = leave_account.rule.depletion_leave_types.all()
    user = leave_account.user
    get_user_depletion_leave_types = user.leave_accounts.exclude(pk=leave_account.pk).filter(
        rule__leave_type__in=depletion_leave_types
    )

    # if depletion policy is archive for user, ignore
    if get_user_depletion_leave_types.filter(is_archived=True).exists():
        return

    # only allow user to take this leave if all depletion leave types have
    # no more than zero balance
    if get_user_depletion_leave_types.filter(usable_balance__gt=0).exists():
        others = ', '.join(
            list(depletion_leave_types.values_list('name', flat=True))
        )
        raise ValidationError(
            f"The leave request on this account requires balance from the "
            f"following accounts to be consumed: {others}"
        )


def validate_require_experience(leave_account):
    """
    Validate if user meets required experience to take the leave
    :return:
    """
    if not leave_account.master_setting.require_experience:
        return
    exp = leave_account.rule.required_experience
    exp_duration = leave_account.rule.required_experience_duration

    if not (exp and exp_duration):
        return

    delta = {
        YEARS: relativedelta(years=exp),
        MONTHS: relativedelta(months=exp),
        DAYS: relativedelta(days=exp)
    }

    doj = nested_getattr(leave_account, 'user.detail.joined_date')
    member_since = relativedelta(
        dt1=timezone.now().date(), dt2=doj
    )
    if relative_delta_gte(delta.get(exp_duration), member_since):
        raise ValidationError(
            "You do not meet required experience duration to apply for this "
            "leave."
        )
    pass


def validate_require_time_period(leave_account, start_timestamp, end_timestamp):
    """
    Raises validation error if the leave_account rule requires to be applied
    on an fixed interval only.
    :return:
    """
    if not leave_account.master_setting.require_time_period:
        return
    # this leave requires to be applied between the following dates.
    apply_after = leave_account.rule.start_date
    apply_before = leave_account.rule.end_date

    errors = []
    if apply_after and start_timestamp.date() < apply_after:
        errors.append(
            f'The leave must be applied after {apply_after}'
        )
    if apply_before and end_timestamp.date() > apply_before:
        errors.append(
            f'The leave must be applied before {apply_before}'
        )
    if errors:
        raise ValidationError(errors)


def require_prior_approval(leave_account, start_timestamp, balance):
    """
    Check prior approval days if exists
    :return:
    """
    flag = leave_account.master_setting.require_prior_approval

    if not (
        flag and leave_account.rule.require_prior_approval
    ):
        return
    category = nested_getattr(leave_account, 'rule.leave_type.category')
    if category and category in [CREDIT_HOUR, TIME_OFF]:
        balance /= 60 
    request_prior_approval = leave_account.rule.prior_approval_rules.filter(
        prior_approval_request_for__lte=balance
    ).order_by('-prior_approval_request_for').first()

    if not request_prior_approval:
        return

    unit = request_prior_approval.prior_approval_unit
    value = request_prior_approval.prior_approval

    delta_before = {
        DAYS: relativedelta(days=value),
        HOURS: relativedelta(hours=value),
        MINUTES: relativedelta(minutes=value),
    }.get(unit)

    if unit == DAYS:
        apply_before = start_timestamp.date() - delta_before
        if get_today() > apply_before:
            raise ValidationError(
                f"The leave request must be sent {value} days before."
            )
    elif unit in [HOURS, MINUTES]:
        apply_before = start_timestamp.astimezone() - delta_before
        if get_today(with_time=True) > apply_before:
            raise ValidationError(
                f"The leave request must be sent {value} {unit.lower()} before."
            )


def require_docs(leave_account, attachment, balance):
    """
    Validates the presence of attachment if it is required by the rule
    :return:
    """
    if not (
        leave_account.master_setting.require_document
        and leave_account.rule.require_docs
    ):
        return
    # Require attachment if start is more than this limit.
    attachment_required_balance = leave_account.rule.require_docs_for
    if balance > attachment_required_balance and not attachment:
        raise ValidationError(
            'A valid attachment is required to apply for this leave for more '
            f'than {attachment_required_balance} balance'
        )


def validate_limit_limitation(leave_account, leave_balance, start_date):
    """

    :return:
    """
    if not leave_account.master_setting.leave_limitations:
        return
    limit_leave_to = leave_account.rule.limit_leave_to
    limit_leave_duration = leave_account.rule.limit_leave_duration
    limit_leave_duration_type = leave_account.rule.limit_leave_duration_type

    if limit_leave_to and limit_leave_to <= 0 or not (
        limit_leave_duration and limit_leave_duration_type
    ):
        return

    leave_since = {
        YEARS:
            start_date - relativedelta(years=limit_leave_duration),
        MONTHS:
            start_date - relativedelta(months=limit_leave_duration)
    }.get(limit_leave_duration_type)

    balance_consumed_in_duration = LeaveSheet.objects.filter(
        request__leave_account=leave_account
    ).exclude(
        request__status=DENIED,
        request__is_deleted=True
    ).filter(
        leave_for__gte=leave_since,
        leave_for__lte=start_date
    ).aggregate(
        consumed=Sum('balance')
    ).get(
        'consumed'
    ) or 0

    # the total balance in duration includes this current leave_balance.
    total_balance_consumed = balance_consumed_in_duration + leave_balance

    if total_balance_consumed > limit_leave_to:
        raise ValidationError(
            f"The total allowed balance in {limit_leave_duration} "
            f"{limit_leave_duration_type} is {limit_leave_to}. You cannot apply"
        )
    return


def validate_continuous_leave(leave_account, leave_balance):
    """
    Raises Validation Error if the leave_balance is less than continuous length
    required or more than max_length allowed.
    :return:
    """
    if not leave_account.master_setting.continuous:
        return

    actual_max_length = leave_account.rule.maximum_continuous_leave_length
    actual_min_length = leave_account.rule.minimum_continuous_leave_length

    year_of_service_for_cl = leave_account.rule.year_of_service
    year_of_service = relativedelta(
        get_today(),
        leave_account.user.detail.joined_date
    )
    year_of_service_for_user = year_of_service.years * 12 + year_of_service.months

    if not year_of_service_for_cl or year_of_service == 0 or year_of_service_for_cl > year_of_service_for_user:
        if actual_min_length and actual_max_length:
            range_str = f"between {actual_min_length} and {actual_max_length}"
        elif actual_min_length and not actual_max_length:
            range_str = f"minimum of {actual_min_length}"
        elif actual_max_length and not actual_min_length:
            range_str = f"maximum of {actual_max_length}"
        else:
            # None of min_length or max length exists
            return

        # if limit set use that limit else take leave balance as the limit
        max_length = actual_max_length or leave_balance
        min_length = actual_min_length or leave_balance

        if not (min_length <= leave_balance <= max_length):
            raise ValidationError(
                f"This leave request consumes {leave_balance}. "
                f"This leave allows leave {range_str}."
            )


def validate_action_permission(leave_request, status, actor):
    """
    Raises validation error if the user is trying to perform action the user
    is not allowed to.
    :param leave_request:
    :param status:
    :return:
    """
    if LEAVE_PERMISSION.get("code") in actor.get_hrs_permissions(
        leave_request.user.detail.organization
    ):
        return  # Do not object if the actor is HR Admin
    supervision = leave_request.user.supervisors.filter(
        supervisor=actor
    ).first()
    if supervision:
        check_attr = {
            FORWARDED: 'forward',
            DENIED: 'deny',
            APPROVED: 'approve'
        }
        if getattr(
            supervision,
            check_attr.get(
                status
            )
        ):
            return
        raise ValidationError(
            f"You cannot perform {status} action on this leave request."
        )

def get_shift_start(user, date, part):
    """
    Returns the start time of user's first shift for the date.
    :param user:
    :param date:
    :return:
    """
    work_day = user.attendance_setting.work_day_for(date)
    if work_day:
        timing = work_day.timings.first()
        append = timing.working_minutes // 2 if part == SECOND_HALF else 0
        time = timing.start_time
        return combine_aware(
            date, time
        ) + timezone.timedelta(
            minutes=append
        )
    return combine_aware(
        date, datetime.time(0, 0)
    )
    # raise ValidationError({
    #     'start':
    #         f"The user does not have a shift for this date."
    # })


def get_shift_end(user, date, part):
    """
    Returns the end time of user's first shift for the date.
    :param user:
    :param date:
    :return:
    """
    work_day = user.attendance_setting.work_day_for(date)
    if work_day:
        timing = work_day.timings.first()
        append = timing.working_minutes // 2 if part == FIRST_HALF else 0
        time = timing.end_time
        shift_end = combine_aware(
            date, time
        ) - timezone.timedelta(
            minutes=append
        )
        if timing.extends:
            shift_end = shift_end + timedelta(days=1)
        return shift_end
    return combine_aware(
        date, datetime.time(23, 59)
    )
    # raise ValidationError({
    #     'end':
    #         f"The user does not have a shift for this date."
    # })


def leave_request_for_timesheet(timesheet, requested_only=True):
    from irhrs.leave.models.request import LeaveSheet

    date = timesheet.timesheet_for
    user = timesheet.timesheet_user
    base_qs = LeaveSheet.objects.exclude(
        # Ignore Deleted Leave Requests
        request__is_deleted=True
    )
    if requested_only:
        qs = base_qs.exclude(
            request__status__in=[DENIED, APPROVED]  # requested only
        )
    else:
        qs = base_qs.exclude(
            request__status=DENIED  # approved too
        )
    qs = qs.filter(
        request__user=user,
        leave_for=date
    )
    return qs


def test_if_payroll_is_generated(user, start):
    """
    The util tests if the payroll for the user is generated for the
    given range

    User should not be able to apply leave, if overtime claim for
    that day is approved and payroll is generated for that day.
    User should not be able to delete leave request if payroll
    generated for that days.
    User should not be able to apply for holidays if holiday
    inclusive is set to false.
    """
    get_last_payroll_generated, exists = get_dependency(
        'irhrs.payroll.utils.helpers.get_last_payroll_generated_date_excluding_simulated'
    )
    last_payroll_generated = get_last_payroll_generated(user)
    return exists and last_payroll_generated and start <= last_payroll_generated


def test_if_overtime_is_claimed(user, start, end):
    """
    The util tests if any overtime for the given range has been claimed.
    """
    return OvertimeClaim.objects.filter(
        overtime_entry__user=user
    ).exclude(
        status__in=[UNCLAIMED, DECLINED]
    ).filter(
        overtime_entry__timesheet__timesheet_for__range=(start, end),
    ).exists()


def is_hourly_account(leave_account):
    return leave_account.rule.leave_type.category in (TIME_OFF, CREDIT_HOUR)


def validate_minimum_maximum_range(leave_account, leave_balance):
    if not is_hourly_account(leave_account):
        return
    leave_duration = timedelta(minutes=leave_balance)
    leave_duration_display = humanize_interval(leave_duration)

    minimum_request_duration_applicable = nested_getattr(
        leave_account,
        'rule.credit_hour_rule.minimum_request_duration_applicable'
    )
    minimum_request_duration = nested_getattr(
        leave_account,
        'rule.credit_hour_rule.minimum_request_duration'
    )
    if minimum_request_duration_applicable and minimum_request_duration > leave_duration:
        minimum = humanize_interval(minimum_request_duration)
        raise ValidationError(
            f"Minimum request limit is {minimum}. Applied: {leave_duration_display}"
        )

    maximum_request_duration_applicable = nested_getattr(
        leave_account,
        'rule.credit_hour_rule.maximum_request_duration_applicable'
    )
    maximum_request_duration = nested_getattr(
        leave_account,
        'rule.credit_hour_rule.maximum_request_duration'
    )

    if maximum_request_duration_applicable and maximum_request_duration < leave_duration:
        maximum = humanize_interval(maximum_request_duration)
        raise ValidationError(
            f"Maximum request limit is {maximum}. Applied: {leave_duration_display}"
        )


def raise_validation_if_payroll_is_generated(user, start_timestamp):
    # Validate if payroll is generated [HRIS-1641]
    if test_if_payroll_is_generated(
        user, start_timestamp
    ):
        raise ValidationError(
            "The Payroll for these days have been generated."
        )


# Adjacent Offday Leave Util
def get_leave_account_for_reduction(leave_request, balance=1):
    this_account = leave_request.leave_account
    if balance <= this_account.usable_balance:
        return [this_account]
    leave_types = tuple(this_account.rule.adjacent_offday_inclusive_leave_types.exclude(
        leave_type=this_account.rule.leave_type.id
    ).values_list('leave_type', flat=True))
    # in case of insufficient balance, search for other leave_account
    other_available_allowed_leave_accounts = this_account.user.leave_accounts.exclude(
        id=this_account.id
    ).filter(
        rule__leave_type__in=leave_types,
        is_archived=False
    ).filter(
        usable_balance__gte=balance
    ).annotate(
        leave_type=F('rule__leave_type')
    ).annotate(
        order_value=Case(
            *[When(leave_type=lt, then=ind) for ind, lt in enumerate(leave_types)],
            default=None,
            output_field=PositiveSmallIntegerField(null=True)
        )
    ).order_by(
        'order_value'
    )
    return other_available_allowed_leave_accounts


def get_coefficient(user, date_):
    if user.is_holiday(date_):
        return HOLIDAY
    elif user.is_offday(date_):
        return OFFDAY
    else:
        return WORKDAY


def send_unable_to_apply_leave_org_notification(user, day):
    text = "Unable to apply leave for %s for %s" % (user, day)
    notify_organization(
        text=text,
        action=user,
        organization=user.detail.organization,
        permissions=[LEAVE_PERMISSION, LEAVE_REQUEST_PERMISSION],
    )


def apply_leave_on_behalf_by_system_if_applicable(leave_request):
    _id = leave_request.id
    flag = leave_request.leave_rule.adjacent_offday_inclusive
    if not flag:
        return
    leave_request = LeaveRequest.objects.get(id=_id)
    ahead = []
    below = []
    user = leave_request.user
    # check if offday/holiday is considered or not
    inclusion_type = leave_request.leave_rule.adjacent_offday_inclusive_type
    allow_holiday = inclusion_type in [INCLUDE_HOLIDAY, INCLUDE_HOLIDAY_AND_OFF_DAY]
    allow_offday = inclusion_type in [INCLUDE_OFF_DAY, INCLUDE_HOLIDAY_AND_OFF_DAY]

    # forward
    for i in range(1, ADJACENT_HOLIDAY_OFFDAY_INCLUSION_DAYS):
        that_day = leave_request.end.astimezone().date() + timezone.timedelta(days=i)
        coefficient = get_coefficient(user, that_day)
        if coefficient == WORKDAY:
            break
        # ensure no leave for that day.
        if allow_holiday and coefficient == HOLIDAY:
            ahead.append(that_day)
        if allow_offday and coefficient == OFFDAY:
            ahead.append(that_day)

    # backward
    for i in range(1, ADJACENT_HOLIDAY_OFFDAY_INCLUSION_DAYS):
        that_day = leave_request.start.astimezone().date() - timezone.timedelta(days=i)
        coefficient = get_coefficient(user, that_day)
        if coefficient == WORKDAY:
            break
        # ensure no leave for that day.
        if allow_holiday and coefficient == HOLIDAY:
            ahead.append(that_day)
        if allow_offday and coefficient == OFFDAY:
            ahead.append(that_day)

    # process
    to_payroll = []
    for day in sorted([*ahead, *below]):
        for account in get_leave_account_for_reduction(leave_request):
            attempt = apply_leave_by_system(account, day, user)
            if attempt:
                # if leave account is unpaid, send to payroll.
                if not account.rule.is_paid:
                    to_payroll.append(AdjacentTimeSheetOffdayHolidayPenalty(
                        leave_account=account,
                        penalty_for=day,
                    ))
                break
        else:
            send_unable_to_apply_leave_org_notification(user, day)
            # if unable to apply, send to payroll.
            to_payroll.append(AdjacentTimeSheetOffdayHolidayPenalty(
                leave_account=leave_request.leave_account,
                penalty_for=day,
            ))
    AdjacentTimeSheetOffdayHolidayPenalty.objects.bulk_create(to_payroll)


def apply_leave_by_system(account, day, user):
    from irhrs.leave.api.v1.serializers.leave_request import AdminLeaveRequestSerializer
    description = 'Forced Leave for %s' % day
    payload = {
        'user': user.id,
        'leave_account': account.id,
        'details': description,
        'start': day,
        'end': day,
        'part_of_day': FULL_DAY
    }
    ser = AdminLeaveRequestSerializer(
        context={
            'request': DummyObject(
                method='POST',
                user=get_system_admin()
            ),
            'organization': user.detail.organization,
            'prevent_default': True,
            'mode': 'hr',
            'bypass_validation': "true"
        },
        data=payload
    )
    if ser.is_valid():
        ser.save()
        return True
    return False

# /Adjacent Offday Leave Util
