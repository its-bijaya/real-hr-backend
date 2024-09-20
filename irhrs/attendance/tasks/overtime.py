import json
import logging
from datetime import timedelta, time

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Subquery
from django.utils import timezone
from django_q.models import Schedule

from irhrs.attendance.constants import WORKDAY, UNCLAIMED, DAILY, WEEKLY, \
    NO_LEAVE, HOLIDAY, FIRST_HALF, SECOND_HALF, TIME_OFF, FULL_LEAVE, OFFDAY, \
    BOTH, PUNCH_IN_ONLY, PUNCH_OUT_ONLY, EITHER, NO_OVERTIME, \
    GENERATE_AFTER_DEDUCTION, DAYS, MONTHS, YEARS, DECLINED
from irhrs.attendance.models import TimeSheet, IndividualUserShift
from irhrs.attendance.tasks.credit_hours import generate_credit_hours_for_approved_credit_hours
from irhrs.attendance.utils.attendance import get_week
from irhrs.core.constants.organization import OVERTIME_UNCLAIMED_EXPIRED

from irhrs.core.utils import nested_getattr, get_system_admin
from irhrs.core.utils.common import get_today, combine_aware, get_yesterday

# before optimizing this import check whether these utils are imported elsewhere
from irhrs.attendance.utils.overtime_utils import *
from irhrs.core.utils.email import send_email_as_per_settings

OVERTIME_ENTRY_CREATED = True
OVERTIME_ENTRY_CREATION_FAILED = False

attendance_logger = logging.getLogger(__name__)


def generate_daily_overtime_entry(timesheet, overtime_setting):
    from irhrs.attendance.models.overtime import OvertimeEntry, \
        OvertimeEntryDetail
    user = timesheet.timesheet_user
    if not overtime_setting:
        attendance_logger.debug(
            f"Failed to create Overtime Entry for {user.full_name}. "
            f"User was valid but overtime setting was Null."
        )
        return
    punch_in_delta = timesheet.punch_in_delta or timedelta(0)
    punch_out_delta = timesheet.punch_out_delta or timedelta(0)
    punch_in_delta = - punch_in_delta
    attendance_logger.debug(
        f"User: {user} Punch In Delta: {punch_in_delta} Punch Out Delta: {punch_out_delta}"
    )
    workday = (
            timesheet.leave_coefficient == NO_LEAVE
            and timesheet.coefficient == WORKDAY
    )
    if (workday and (
            not punch_in_delta or
            timezone.timedelta(
                minutes=overtime_setting.applicable_before
            ) > punch_in_delta
    ) and (
            not punch_out_delta or
            timezone.timedelta(
                minutes=overtime_setting.applicable_after) >
            punch_out_delta
    )):
        attendance_logger.debug(
            f"Failed to create Overtime Entry for {user.full_name}. Because "
            f"both punch_in and punch_out deltas were smaller than decided "
            f"limit. "
            f"User Punch In: {punch_in_delta} "
            f"User Punch Out: {punch_out_delta} "
            f"Required Before: {overtime_setting.applicable_before} "
            f"Required After: {overtime_setting.applicable_after}"
        )
        return OVERTIME_ENTRY_CREATION_FAILED

    leave_coefficient = timesheet.leave_coefficient
    coefficient = timesheet.coefficient

    if leave_coefficient in [NO_LEAVE, FIRST_HALF,
                             SECOND_HALF] and coefficient == WORKDAY:
        entry_object = OvertimeEntry(
            user=user,
            overtime_settings=overtime_setting,
            timesheet=timesheet
        )
        attendance_logger.debug(
            f"Calibrating If the user has worked enough to claim overtime"
        )
        early_overtime, late_overtime = get_early_late_overtime(
            timesheet,
            overtime_setting
        )
        attendance_logger.debug(
            f"Calibrated {early_overtime} as early and {late_overtime} as late"
        )
        flat_rejection_value = timedelta(
            minutes=overtime_setting.flat_reject_value
        )
        total_overtime = early_overtime + late_overtime
        if (
                total_overtime < flat_rejection_value
                or total_overtime == ZERO_OVERTIME
        ):
            attendance_logger.debug(
                f"Failed to create overtime for {user} on "
                f"{timesheet.timesheet_for} as total overtime is less than "
                f"{flat_rejection_value}."
            )
            return OVERTIME_ENTRY_CREATION_FAILED
        entry_object.save()
        overtime_entry_detail = dict(
            punch_in_overtime=early_overtime,
            punch_out_overtime=late_overtime,
            overtime_entry=entry_object
        )
        OvertimeEntryDetail.objects.create(**overtime_entry_detail)

        # Post Save Calculation for OvertimeEntry Detail.
        # 1. Claimed Overtime is Generated as Total Overtime Calculated by
        # system
        # 2. Claimed Overtime is filtered according to the overtime settings.
        # 3. Normalized overtime is calculated according to the rates in
        # Overtime settings versus the claimed overtime.
        #
        # NOTE: Early and Late overtime is editable by the user,
        #   which recomputes the below steps.

        return entry_object
    else:
        # For Offday, Holiday, Full Leave
        coefficient_setting = {
            OFFDAY: 'off_day_overtime',
            HOLIDAY: 'paid_holiday_affect_overtime',
            WORKDAY: 'leave_affect_overtime'
        }.get(coefficient)
        enabled = getattr(overtime_setting, coefficient_setting, None)
        if not enabled:
            return
        else:
            attendance_logger.debug(
                f"Calibrating {coefficient} "
                f"overtime for {user} for {timesheet.timesheet_for}"
            )
            entry_object = OvertimeEntry(
                user=user,
                overtime_settings=overtime_setting,
                timesheet=timesheet
            )
            # check `overtime_after_offday`
            # reduce overtime if compensatory leave is generated.
            overtime = get_off_day_overtime(timesheet, overtime_setting)
            flat_rejection_value = overtime_setting.flat_reject_value
            if overtime <= timedelta(minutes=flat_rejection_value):
                return
            entry_object.save()
            overtime_entry_detail = dict(
                punch_in_overtime=slot_trim_overtime(overtime, overtime_setting),
                punch_out_overtime=timezone.timedelta(minutes=0),
                overtime_entry=entry_object
            )
            OvertimeEntryDetail.objects.create(**overtime_entry_detail)
        return entry_object


def generate_overtime_claim(overtime_entry, description=''):
    from irhrs.attendance.models import OvertimeClaim
    user = overtime_entry.user
    overtime_claim = OvertimeClaim(
        overtime_entry=overtime_entry,
        description=description,
        recipient=user,
        status=UNCLAIMED
    )
    overtime_claim.save()
    overtime_claim.overtime_histories.create(
        action_performed=UNCLAIMED,
        action_performed_by=get_system_admin(),
        action_performed_to=user,
        remark="Overtime Generated by the System."
    )


def generate_overtime_entry_for_range(
        start_date, end_date, ot_type,
        fix_missing=False,
        fix_ids=list()
):
    from irhrs.attendance.models import OvertimeEntry
    attendance_with_shifts = IndividualUserShift.objects.filter(
        Q(applicable_to__isnull=True) |
        Q(applicable_to__gte=timezone.now().date())
    ).values('individual_setting')
    valid_users_for_overtime = get_user_model().objects.filter(
        attendance_setting__in=attendance_with_shifts,
        attendance_setting__overtime_setting__isnull=False,
        attendance_setting__overtime_setting__overtime_calculation=ot_type,
        attendance_setting__enable_overtime=True
    ).exclude(
        # These excluded OTs are handled through its own BG Task as Pre Approval OT
        attendance_setting__overtime_setting__require_prior_approval=True
    )
    timesheets = TimeSheet.objects.filter(
        overtime__isnull=True,
        timesheet_user__in=valid_users_for_overtime,
        punch_in__isnull=False,
        punch_out__isnull=False
    ).exclude(
        coefficient=WORKDAY,
        work_shift__isnull=True
    ).select_related(
        'timesheet_user',
        'timesheet_user__attendance_setting',
        'timesheet_user__attendance_setting__overtime_setting',
    )
    if fix_missing:
        # generate_adjusted_overtime
        timesheets = timesheets.filter(
            id__in=fix_ids
        )
    else:
        timesheets = timesheets.filter(
            timesheet_for__gte=start_date,
            timesheet_for__lte=end_date,
        )
    entries = list()
    for timesheet in timesheets:
        user = timesheet.timesheet_user
        attendance_setting = getattr(user, 'attendance_setting', None)
        if not attendance_setting:
            attendance_logger.warning(
                f'No attendance setting for user '
                f'{user.full_name}. Failed to generate Overtime Claim!'
            )
            continue
        overtime_setting = attendance_setting.overtime_setting
        if not overtime_setting:
            attendance_logger.warning(
                f'No overtime setting for user {user.full_name}. Failed to '
                f'generate Overtime Claim!'
            )
            continue
        entry = generate_daily_overtime_entry(timesheet, overtime_setting)
        if isinstance(entry, OvertimeEntry):
            entries.append(entry)
    return entries


@transaction.atomic()
def generate_overtime(
        start_date, end_date, ot_type, fix_missing=False, fix_ids=list()
):
    """
    timezone.now() + timezone.timedelta(
        days=-1 * TOTAL_WEEK_DAYS)
    :return:
    """
    entries = generate_overtime_entry_for_range(
        start_date, end_date, ot_type,
        fix_missing=fix_missing, fix_ids=fix_ids
    )
    entries_count = len(entries)
    attendance_logger.debug(
        f"Created {entries_count} entries"
    )
    from irhrs.attendance.models import OvertimeEntry
    created_entries = list()
    for entry in entries:
        if isinstance(entry, OvertimeEntry):
            ot_detail = entry.overtime_detail
            # make claimed overtime total instead of claimable.
            ot_detail.claimed_overtime = timedelta(
                seconds=ot_detail.total_seconds
            )
            ot_detail.normalized_overtime = timedelta(
                seconds=ot_detail.normalized_overtime_seconds
            )
            ot_detail.save()
            attendance_logger.debug(
                f'Generating Overtime Claim of {entry.user.full_name} for '
                f'{entry.timesheet.timesheet_for}'
            )
            generate_overtime_claim(entry)
            created_entries.append(entry)
    from irhrs.attendance.utils.overtime import \
        generate_overtime_notification, send_overtime_email
    generate_overtime_notification(entries=created_entries)
    send_overtime_email(entries=created_entries)
    if fix_missing:
        return {
            'created_count': entries_count,
            'created_entries': list(
                map(
                    str,
                    sorted(created_entries, key=lambda x: x.timesheet.id)
                )
            )
        }
    return {
        'created_count': entries_count,
        'created_entries': list(
            map(
                str,
                sorted(created_entries, key=lambda x: x.user.full_name)
            )
        )
    }


def generate_daily_overtime(success_date, schedule_next_task=True):
    from irhrs.attendance.signals import recalibrate_overtime

    base_qs = TimeSheet.objects.filter(
        modified_at__gte=parse(success_date)
    )
    fix_ids = list(base_qs.filter(overtime__isnull=True).values_list(
        'id', flat=True
    ))
    time_begin = timezone.now().isoformat()
    new_overtime = generate_overtime(
        '', '', ot_type=DAILY, fix_missing=True, fix_ids=fix_ids
    )
    recalibrates = base_qs.filter(
        overtime__isnull=False,
        overtime__claim__status__in=(UNCLAIMED, DECLINED)
    )
    successful_recalibrates = list()
    for recalibrate in recalibrates:
        recalibrated, _ = recalibrate_overtime(
            recalibrate, get_system_admin(), None
        )
        if recalibrated:
            successful_recalibrates.append(recalibrate)

    if schedule_next_task:
        Schedule.objects.filter(
            func='irhrs.attendance.tasks.overtime.generate_daily_overtime'
        ).update(
            args=(time_begin,)
        )
    from irhrs.attendance.tasks.pre_approval import generate_overtime_entry_for_pre_approved_ot
    pre_approval_overtime = generate_overtime_entry_for_pre_approved_ot()
    generate_credit_hours_for_approved_credit_hours()
    return {
        "re-calibrated": successful_recalibrates,
        "new_overtimes": new_overtime,
        "pre approval": pre_approval_overtime
    }


def generate_weekly_overtime(week_timestamp=None):
    try:
        date = parse(week_timestamp).date()
    except (TypeError, ValueError):
        date = timezone.now().date()
    start, end = get_week(date)
    next_week = (timezone.now() + relativedelta(weeks=1)).isoformat()
    ret = generate_overtime(start, end, WEEKLY)
    Schedule.objects.filter(
        func='irhrs.attendance.tasks.overtime.generate_weekly_overtime'
    ).update(
        args=(next_week,)
    )
    return ret


def generate_overtime_for_range_str(start_date, end_date, ot_type):
    # This for testing to test generating overtime for given range
    # parse string to date
    import dateutil
    start_date = dateutil.parser.parse(start_date).date()
    end_date = dateutil.parser.parse(end_date).date()
    return generate_overtime(start_date, end_date, ot_type)


def valid_timesheet_for_ot_regeneration(timesheet):
    """
    Valid only if:
        * timesheet user -> setting -> ot setting enabled. # skipping this.
        will be checked above.
        * its generation was expected to be in the past.
    """
    user = timesheet.timesheet_user
    # Prior Approval OT is invalid for recalibration.
    if nested_getattr(
        user,
        'attendance_setting__overtime_setting__require_prior_approval',
        separator='__'
    ):
        return 'Invalid'
    ot_type = nested_getattr(
        user,
        'attendance_setting__overtime_setting__overtime_calculation',
        separator='__'
    )
    today = get_today()
    end_of_week = get_week(today)
    deadline = {
        DAILY: today - timedelta(days=1),
        WEEKLY: end_of_week[1]
    }.get(
        ot_type,
        today
    )
    exists = hasattr(timesheet, 'overtime')
    if exists:
        return 'Exists'
    return 'Valid' if deadline < today else 'Invalid'


def fix_missing_daily(fix_ids):
    # ignore start/end time.
    return generate_overtime(
        '', '', ot_type=DAILY, fix_missing=True, fix_ids=fix_ids
    )


def fix_missing_weekly(fix_ids):
    return generate_overtime(
        '', '', ot_type=WEEKLY, fix_missing=True, fix_ids=fix_ids
    )


def generate_adjusted_overtime(timesheet):
    """
    Use this from adjustment approval page or offline attendance page.
    :param timesheet: Check to see if this timesheet missed its chance of
    getting generated.
    :return:
    """
    overtime_test = valid_timesheet_for_ot_regeneration(timesheet)
    if overtime_test == 'Valid':
        midnight = combine_aware(
            timezone.now().date() + timezone.timedelta(days=1), time(2, 0)
        )
        calculation_type = nested_getattr(
            timesheet.timesheet_user,
            'attendance_setting__overtime_setting__overtime_calculation',
            separator='__'
        )
        function_mapper = {
            DAILY: 'fix_missing_daily',
            WEEKLY: 'fix_missing_weekly'
        }
        # function is generate_overtime
        # Add new params
        # { fix_missing: True, ids=[]}
        # Time Sheet filter procedure will look at these ids only.
        func = function_mapper.get(
            calculation_type
        )
        identifier = f'Generate Fix missing for {get_today()}'
        obj, created = Schedule.objects.get_or_create(
            func=f'irhrs.attendance.tasks.overtime.{func}',
            name=identifier,
            schedule_type=Schedule.ONCE,
            next_run=midnight,
        )
        if created:
            params = {
                'fix_ids': [timesheet.id]
            }
        else:
            kwargs = json.loads(obj.kwargs)
            kwargs.get('fix_ids').append(timesheet.id)
            params = kwargs
        obj.kwargs = json.dumps(params)
        obj.save()
    else:
        return overtime_test


def expire_claims():
    """
    Expires the overtime claims.
    The claims will be archived, so the timesheet will not be able to
    generate claims again.
    The archived claims will be unreachable by the user.
    """
    today = get_today()
    from irhrs.attendance.models import OvertimeSetting
    from irhrs.attendance.models import OvertimeClaim
    expiration_settings = Subquery(OvertimeSetting.objects.filter(
        claim_expires=True
    ).values_list('id', flat=True))
    qs = OvertimeClaim.objects.filter(
        overtime_entry__overtime_settings__in=expiration_settings,
        status=UNCLAIMED
    ).select_related(
        'overtime_entry',
        'overtime_entry__overtime_settings'
    )
    for ot in qs:
        setting = ot.overtime_entry.overtime_settings
        expires_after = setting.expires_after
        expires_after_unit = setting.expires_after_unit

        expiration_delta = {
            DAYS: relativedelta(days=expires_after),
            MONTHS: relativedelta(months=expires_after),
            YEARS: relativedelta(years=expires_after),
        }.get(
            expires_after_unit
        )
        if ot.created_at.date() + expiration_delta < today:
            ot.is_archived = True
            ot.save()
            subject = "Overtime Expired"
            email_text = f"Overtime for {ot.created_at.date()} has been expired."
            send_email_as_per_settings(
                recipients=ot.recipient,
                subject=subject,
                email_text=email_text,
                email_type=OVERTIME_UNCLAIMED_EXPIRED
            )
