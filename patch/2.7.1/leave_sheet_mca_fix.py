from django.db import transaction
from django.db.models import Min, Max, Avg
from rest_framework.exceptions import ValidationError

from irhrs.leave.constants.model_constants import TIME_OFF, CREDIT_HOUR
from irhrs.leave.models import LeaveRequest


def recalculate_leave_sheet(leave_account, user, start_time, end_time):
    leave_category = leave_account.rule.leave_type.category
    # In case of Time Off/Credit Hour the balance deducted is the minutes of leave.
    workday = user.attendance_setting.work_day_for(end_time)
    errors = list()
    if not workday:
        errors.append({
            'start_time': 'User has no shift for the day.'
        })
    else:
        timings = workday.timings.aggregate(
            sh_start=Min('start_time'),
            sh_end=Max('end_time'),
            sh_time=Avg('working_minutes')
        )
        shift_start = timings.get('sh_start')
        shift_end = timings.get('sh_end')
        shift_minutes = timings.get('sh_time')
        if leave_category == TIME_OFF:
            if shift_start > start_time.astimezone().time():
                errors.append({
                    'start_time': f'The shift begins at {shift_start}'
                })
            if shift_end < end_time.astimezone().time():
                errors.append({
                    'end_time': f'The shift ends at {shift_end}'
                })
        elif leave_category == CREDIT_HOUR:
            if start_time.astimezone().time() < shift_start:
                errors.append({
                    'start_time': f'The shift begins at {shift_start}. '
                                  f'Please select time after the shift begins.'
                })
            if end_time.astimezone().time() > shift_end:
                errors.append({
                    'end_time': f'The shift ends at {shift_end}. '
                                'Please select time before the shift ends.'
                })
    if errors:
        raise ValidationError(errors)
    time_delta = end_time - start_time
    if time_delta.total_seconds() < 0:
        # invalid request
        raise ValidationError(
            "The start time cannot be greater than end time."
        )
    else:
        balance_minutes = int(time_delta.total_seconds() / 60)
        if (
                start_time.astimezone().time() == shift_start
                and end_time.astimezone().time() == shift_end
        ):
            return balance_minutes, [
                {
                    'leave_for': start_time.date(),
                    'start_time': start_time,
                    'end_time': end_time,
                    'balance': 1,
                    'balance_minutes': 0
                }
            ]
        half_time = int(shift_minutes/2)
        if balance_minutes >= half_time and (
                start_time.astimezone().time() == shift_start
                or end_time.astimezone().time() == shift_end
        ):
            return balance_minutes, [
                {
                    'leave_for': start_time.date(),
                    'start_time': start_time,
                    'end_time': end_time,
                    'balance': 0.5,
                    'balance_minutes': (balance_minutes-half_time)
                }
            ]

        return balance_minutes, [
            {
                'leave_for': start_time.date(),
                'start_time': start_time,
                'end_time': end_time,
                'balance': 0,
                'balance_minutes': balance_minutes
            }
        ]


def recalculate():
    leave_requests_to_recalculate = LeaveRequest.objects.filter(
        leave_rule__leave_type__category=CREDIT_HOUR,
        start__date__gte='2020-04-01',
    )
    for leave_request in leave_requests_to_recalculate:
        try:
            balance, sheets = recalculate_leave_sheet(
                leave_request.leave_account,
                leave_request.user,
                leave_request.start.astimezone(),
                leave_request.end.astimezone()
            )
        except:
            print(leave_request.user, leave_request.start.date(), 'shift changed')
            continue
        leave_request.balance = balance
        leave_request.save()
        sheet = leave_request.sheets.first()
        if not sheet:
            leave_request.sheets.create(
                leave_for=leave_request.start.date(),
                start=leave_request.start,
                end=leave_request.end,
                balance=sheets[0].get('balance'),
                balance_minutes=sheets[0].get('balance_minutes')
            )
        else:
            sheet.balance = sheets[0].get('balance')
            sheet.balance_minutes = sheets[0].get('balance_minutes')
            sheet.save()


with transaction.atomic():
    recalculate()
