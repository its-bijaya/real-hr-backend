from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone

from irhrs.attendance.constants import WORKDAY, FULL_LEAVE, LATE_IN, EARLY_OUT, PUNCH_OUT
from irhrs.attendance.models import IndividualUserShift


def get_lost_hours_for_date_range(
    user_id, organization, start, end, calculate_unpaid_breaks=True,
    calculate_lost_hour_in_absent_days=False, ignore_seconds=False
):
    # Note: for some clients we do not calculate unpaid breaks
    attendance_with_shifts = IndividualUserShift.objects.filter(
        individual_setting__user_id=user_id
    ).filter(
        Q(applicable_to__isnull=True) |
        Q(applicable_to__gte=timezone.now().date())
    ).values('individual_setting')
    queryset = get_user_model().objects.filter(
        id=user_id,
        attendance_setting__isnull=False,
        attendance_setting__in=attendance_with_shifts,
        detail__organization=organization
    )

    fil = {
        'timesheets__timesheet_for__gte': start,
        'timesheets__timesheet_for__lte': end,
        'timesheets__coefficient': WORKDAY
    }
    excludes = Q(Q(timesheets__leave_coefficient=FULL_LEAVE ) | Q(timesheets__is_present=False))
    if calculate_lost_hour_in_absent_days:
        excludes = Q(timesheets__leave_coefficient=FULL_LEAVE )

    _filters = Q(
        timesheets__timesheet_entries__category = LATE_IN, 
        timesheets__timesheet_entries__is_deleted=False, ** fil
    ) & ~excludes
    lost_late_in = get_irregularity_data_in_seconds(
        queryset, 'timesheets__punch_in_delta', _filters, ignore_seconds)
    _filters = Q(
        timesheets__timesheet_entries__category=EARLY_OUT, 
        timesheets__timesheet_entries__is_deleted=False, **fil
    ) & ~excludes
    lost_early_out = get_irregularity_data_in_seconds(
        queryset, 'timesheets__punch_out_delta', _filters, ignore_seconds)

    lost_absent = 0
    for entries in queryset.filter(
        Q(timesheets__is_present=False, **fil) & ~excludes
    ).values('timesheets__expected_punch_in', 'timesheets__expected_punch_out'):
        expected_punch_out = entries['timesheets__expected_punch_out']
        expected_punch_in = entries['timesheets__expected_punch_in']
        lost_absent_in_seconds = (expected_punch_out - expected_punch_in).total_seconds()
        if ignore_seconds:
            lost_absent += lost_absent_in_seconds // 60 * 60
            continue
        lost_absent += lost_absent_in_seconds

    if calculate_unpaid_breaks:
        _filters = Q(
            timesheets__timesheet_entries__entry_type=PUNCH_OUT,
            timesheets__timesheet_entries__is_deleted=False,
            timesheets__unpaid_break_hours__isnull=False,
            **fil
        ) & ~excludes
        total_unpaid_hours = get_irregularity_data_in_seconds(
            queryset, 'timesheets__unpaid_break_hours', _filters, ignore_seconds)
        return lost_late_in + lost_early_out + lost_absent + total_unpaid_hours

    return lost_late_in + lost_early_out + lost_absent


def get_irregularity_data_in_seconds(queryset, field, fil, ignore_seconds):
    total_lost_seconds = list(queryset.filter(fil).values_list(field, flat=True))
    if not total_lost_seconds:
        return 0

    final_lost_seconds = 0

    for total_lost_second in total_lost_seconds:
        total_seconds = abs(total_lost_second.total_seconds())
        if not ignore_seconds:
            final_lost_seconds += total_seconds
            continue

        final_lost_seconds += total_seconds // 60 * 60

        if field == "timesheets__punch_out_delta" and total_seconds % 60 > 0:
            final_lost_seconds += 60

    return final_lost_seconds

