from datetime import timedelta

from dateutil import rrule
from django.utils import timezone

from irhrs.attendance.api.v1.tests.factory import (
    IndividualAttendanceSettingFactory,
    CreditHourSettingFactory, WorkShiftFactory, WorkShiftFactory2
)
from irhrs.attendance.constants import (
    REQUESTED, FORWARDED, CANCELLED, APPROVED, DECLINED,
    CREDIT_HOUR, APPROVED, CREDIT_HOUR_STATUS_CHOICES, PUNCH_IN, PUNCH_OUT
)
from irhrs.attendance.models import CreditHourRequest, CreditHourRequestHistory, TimeSheet, \
    IndividualAttendanceSetting, IndividualUserShift, CreditHourDeleteRequest
from irhrs.attendance.tasks.credit_hours import generate_credit_hours_for_approved_credit_hours, \
    revert_credit_hour_from_leave_account
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import get_yesterday, combine_aware
from irhrs.leave.api.v1.tests.factory import LeaveAccountFactory, LeaveRuleFactory, \
    LeaveTypeFactory, MasterSettingFactory
from irhrs.leave.constants.model_constants import ADDED, DEDUCTED
from irhrs.leave.models import LeaveAccountHistory
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.users.api.v1.tests.factory import UserFactory


def assign_credit_hour_to_user(user, credit_setting, status=APPROVED):
    assert user.attendance_setting, "User has not been assigned attendance_setting"
    attendance_setting = user.attendance_setting
    attendance_setting.enable_credit_hour = True
    attendance_setting.credit_hour_setting = credit_setting
    attendance_setting.save()


def maintain_credit_hour_history(instance, status, sender, recipient, remarks):
    CreditHourRequestHistory.objects.create(
        credit_hour=instance,
        action_performed=status,
        remarks=remarks,
        action_performed_by=sender,
        action_performed_to=recipient,
    )


def create_credit_history(duration, date, status, sender):
    recipient = UserFactory()
    instance = CreditHourRequest.objects.create(**{
        'request_remarks': 'remarks',
        'credit_hour_duration': duration,
        'credit_hour_date': date,
        'status': REQUESTED,
        'is_deleted': False,
        'sender': sender,
        'recipient': recipient,
    })
    maintain_credit_hour_history(instance, REQUESTED, sender, recipient, REQUESTED)
    if status in (APPROVED, DECLINED):
        CreditHourRequest.objects.filter(**{
            'credit_hour_duration': duration,
            'credit_hour_date': date,
            'status': REQUESTED,
            'sender': sender,
        }).update(status=status)
        maintain_credit_hour_history(instance, status, sender, recipient, status)
    instance.refresh_from_db()
    return instance


def create_delete_credit_history(request, sender, status=APPROVED):
    recipient = UserFactory()
    instance = CreditHourDeleteRequest.objects.create(**{
        'status': REQUESTED,
        'request': request,
        'sender': sender,
        'recipient': recipient,
        'request_remarks': REQUESTED,
    })
    if status in (APPROVED, DECLINED):
        CreditHourDeleteRequest.objects.filter(**{
            'request': request,
        }).update(status=status)
    instance.refresh_from_db()
    return instance


def create_credit_hour_request(
    user, date, payload_duration=timedelta(hours=2), leave_max_balance=120, balance=0,
):
    org = OrganizationFactory()
    detail = user.detail
    detail.organization = org
    detail.save()
    setting, _ = IndividualAttendanceSetting.objects.update_or_create(
        user=user,
        defaults=dict(
            enable_credit_hour=True,
            credit_hour_setting=CreditHourSettingFactory(
                organization=org,
            ),
        )
    )
    IndividualUserShift.objects.create(
        individual_setting=setting,
        shift=WorkShiftFactory2(work_days=7, organization=org),
        applicable_from=timezone.now() - timezone.timedelta(days=365)
    )
    LeaveAccountFactory(
        rule=LeaveRuleFactory(
            leave_type=LeaveTypeFactory(
                category=CREDIT_HOUR,
                master_setting=MasterSettingFactory(organization=org,
                                                    effective_from=get_yesterday())
            ),
            max_balance=leave_max_balance
        ),
        user=user,
        balance=balance,
        usable_balance=balance,
    )
    # create a declined request.
    instance = create_credit_history(
        payload_duration, date, APPROVED, user
    )
    generate_credit_hours_for_approved_credit_hours()
    return instance


def populate_timesheets_for(user, start, end=None):
    if not end:
        TimeSheet.objects._create_or_update_timesheet_for_profile(user, start)
        return TimeSheet.objects.filter(timesheet_for=start, timesheet_user=user).first()
    to_process = list(rrule.rrule(rrule.DAILY, dtstart=start, until=end))
    for day in to_process:
        TimeSheet.objects._create_or_update_timesheet_for_profile(user, day)
    return TimeSheet.objects.filter(timesheet_for__in=to_process, timesheet_user=user).order_by(
        'timesheet_for'
    ).iterator()


def punch_for_credit_hour(
    user, date, early=0, late=0
) -> TimeSheet:
    """Punch given minutes for in and out

    Args:
        user (User): TimeSheet User
        date (timesheet_for): Date
        early (int, optional): Minutes before punch in time. Defaults to 0.
        late (int, optional): Minutes after punch out time. Defaults to 0.

    Returns:
        TimeSheet: Timesheet for user on that day
    """
    timesheet = populate_timesheets_for(user, start=date)
    assert timesheet, "TimeSheet could not be created."
    assert timesheet.expected_punch_out, "Punch Out should not be null"
    TimeSheet.objects.clock(
        user,
        timesheet.expected_punch_in + timezone.timedelta(minutes=early),
        'Device',
        remark_category=PUNCH_IN
    )
    TimeSheet.objects.clock(
        user,
        timesheet.expected_punch_out + timezone.timedelta(minutes=late),
        'Device',
        remark_category=PUNCH_OUT
    )
    return timesheet


def print_leave_histories(leave_account):
    for history in leave_account.history.order_by('created_at'):
        print(
            history.created_at.time(),
            history.id,
            leave_account.user.full_name.ljust(20)[:20],
            str(history.previous_usable_balance).ljust(10),
            str(history.previous_balance).ljust(10),
            str(history.new_usable_balance).ljust(10),
            str(history.new_balance).ljust(10),
            history.remarks,
        )
    print('\n<=================')


def force_balance(leave_account, difference=0):
    leave_account.refresh_from_db()
    new_balance = leave_account.balance + difference
    new_usable = leave_account.usable_balance + difference
    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),
        action=ADDED if difference else DEDUCTED,
        previous_balance=leave_account.balance,
        previous_usable_balance=leave_account.usable_balance,
        new_balance=new_balance,
        new_usable_balance=new_usable,
        remarks="Forced balance %s by system." % difference
    )
    leave_account.balance = new_balance
    leave_account.usable_balance = new_usable
    account_history.save()
    leave_account.save()
