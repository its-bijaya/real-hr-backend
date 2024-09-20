"""
Author: @raw-V

"""
from django.forms.models import model_to_dict
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from irhrs.attendance.constants import HOLIDAY, WORKDAY, OFFDAY
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.models import IndividualUserShift, TimeSheet
from irhrs.core.utils.common import combine_aware

USER = get_user_model()
PROVIDED_EMAILS = [
    'shrijana.shrestha@rojgari.com',
    'shova.bakhu@rojgari.com',
    'shrijana.shrestha@rojgari.com',
    'shova.bakhu@rojgari.com',
    'madan.giri@rojgari.com',
    'ujwal.shrestha@merojob.com',
    'raju.bhattarai@aayulogic.com',
    'prahlad.shrestha@aayulogic.com',
    'sanjeev.shrestha@aayulogic.com',
    'rohit.shrestha@aayulogic.com',
    'prabin.acharya@aayulogic.com',
    'pujan.shrestha@aayulogic.com',
    'santosh.aryal@aayulogic.com',
    'umesh.chaudhary@aayulogic.com',
    'sumit.chhetri@aayulogic.com',
    'babin.subedi@merojob.com',
    'reza.khanal@merojob.com',
    'nisha.gyawali@merojob.com',
    'yagyashree.dahal@merojob.com',
    'priyanka.basnet@merojob.com',
    'rajesh.manandhar@merojob.com',
    'mukesh.ghising@merojob.com',
    'ajay.shrestha@aayulogic.com',
    'sandip.balami@rojgari.com',
    'sujan.chitrakar@merojob.com',
    'kamala.khanal@aayulogic.com',
    'shital.luitel@aayulogic.com',
    'niroj.maharjan@rojgari.com',
    'kritika.katwal@merojob.com',
    'sumit.dhital@rojgari.com',
]
DATE_START = '2020-03-01'
DATE_UNTIL = '2020-03-24'


def m2d(instance):
    return model_to_dict(
        instance,
        fields=[field.name for field in instance._meta.fields]
    )


def produce_list_of_users_whose_work_shift_was_nullified(
        date_start, date_until, provided_emails, read_only=True
):
    # Between the one week period, we test users whose shift was removed.
    shift_removed_users = IndividualUserShift.objects.filter(
        individual_setting__user__email__in=provided_emails,
        applicable_to__isnull=False,
        applicable_to__range=(date_start, date_until)
    )
    for sru in shift_removed_users:
        print(
            str(sru.individual_setting.user.full_name),
            str(sru.shift),
            str(sru.applicable_from),
            str(sru.applicable_to),
        )
    if read_only:
        return
    probable_users = set(shift_removed_users.values_list('individual_setting__user', flat=True))
    for shift_removed_user in shift_removed_users:
        # We make sure, there is no new shift. As we do not want overlapping between shifts for the same user.
        new_one = IndividualUserShift.objects.filter(
            individual_setting=shift_removed_user.individual_setting,
            applicable_from__gt=shift_removed_user.applicable_to
        ).order_by(
            'applicable_from'
        ).first()
        if new_one:
            # If there is a Shift, and luckily, it was set one day after the shift removal, we want no gaps.
            applicable_to = max([
                shift_removed_user.applicable_to,
                new_one.applicable_from - relativedelta(days=1)
            ])
        else:
            applicable_to = None
        print(
            shift_removed_user.individual_setting.user,
            "'s shift's end date has been",
            f'set to {applicable_to}' if applicable_to else 'removed'
        )
        shift_removed_user.applicable_to = applicable_to
        shift_removed_user.save(update_fields=['applicable_to'])

    save_and_process_time_sheet_entries(
        date_start=date_start,
        date_until=date_until,
        probable_users=probable_users
    )


def save_and_process_time_sheet_entries(date_start, date_until, probable_users):
    """
    Now that the user's Work Shift settings has been fixed.
    We need to clean up the time_sheets.
    """
    for time_sheet in TimeSheet.objects.filter(
        timesheet_for__range=(date_start, date_until),
        timesheet_user__in=probable_users
    ):
        fix_time_sheet(time_sheet)


def fix_time_sheet(time_sheet):
    """
    This method will be used to FIX time sheets,
    Apply leave and holidays

    Fix time sheets for every user on  daily basis
    If the user has requested leave we create time shift for that day
    """
    user = time_sheet.timesheet_user
    date_ = time_sheet.timesheet_for
    d1 = m2d(time_sheet)

    def get_coefficient():
        if user.is_holiday(date_):
            return HOLIDAY
        elif user.is_offday(date_):
            return OFFDAY
        else:
            return WORKDAY

    user.attendance_setting.force_prefetch_for_work_shift = True
    user.attendance_setting.force_work_shift_for_date = date_
    shift = user.attendance_setting.work_shift

    if not shift:
        return None
    try:
        day = shift.days[0]
    except IndexError:
        # This means, its off-day.
        day = None
    if day:
        for time in day.work_times:
            defaults = {
                'coefficient': get_coefficient(),
                'expected_punch_in': combine_aware(
                    date_,
                    time.start_time
                ),
                'work_time': time,
                'work_shift': shift,
                'expected_punch_out': combine_aware(
                    date_ + timezone.timedelta(days=1),
                    time.end_time
                ) if time.extends else combine_aware(
                    date_,
                    time.end_time
                )
            }
            for attribute, value in defaults.items():
                setattr(time_sheet, attribute, value)
            time_sheet.save()
    else:
        time_sheet.coefficient = get_coefficient()
        time_sheet.work_shift = shift
        time_sheet.save()
    fix_entries_on_commit(time_sheet, send_notification=False)
    d2 = m2d(time_sheet)
    diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
    print(
        time_sheet,
        'was modified as follows:',
        dict(diffs)
    )


with transaction.atomic():
    produce_list_of_users_whose_work_shift_was_nullified(
        DATE_START,
        DATE_UNTIL,
        PROVIDED_EMAILS,
        read_only=False
    )
