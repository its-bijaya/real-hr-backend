import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction

from irhrs.attendance.constants import APPROVED, REQUESTED, CONFIRMED
from irhrs.attendance.models import TimeSheet, OvertimeEntry
from irhrs.attendance.models.overtime import OvertimeEntryDetail, OvertimeClaim
from irhrs.attendance.models.pre_approval import PreApprovalOvertime
from irhrs.attendance.tasks.overtime import get_early_late_overtime
from irhrs.attendance.utils.helpers import get_pre_approval_recipient
from irhrs.attendance.utils.overtime import generate_overtime_notification
from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.notification.utils import add_notification

logger = logging.getLogger(__name__)
REQUIRE_CONFIRM = getattr(settings, 'REQUIRE_PRE_APPROVAL_CONFIRMATION', False)


def generate_overtime_claim_for_pre_approved_ot(
        overtime_entry, pre_approval, pre_approval_setting
):
    if pre_approval_setting.require_post_approval_of_pre_approved_overtime:
        # if needs to be re-requested
        status_performed = REQUESTED
        recipient = get_pre_approval_recipient(
            pre_approval.sender, status=REQUESTED
        )
    else:
        status_performed = APPROVED
        recipient = pre_approval.recipient
    overtime_claim = OvertimeClaim(
        overtime_entry=overtime_entry,
        description=pre_approval.request_remarks,
        recipient=recipient,
        status=status_performed
    )
    overtime_claim.save()
    notification_text = "Overtime claim of {} for {} has been {}".format(
        pre_approval.sender,
        pre_approval.overtime_date,
        status_performed
    )
    overtime_claim.overtime_histories.create(
        action_performed=status_performed,
        action_performed_by=get_system_admin(),
        action_performed_to=recipient,
        remark=notification_text
    )


@transaction.atomic()
def generate_overtime_entry_for_pre_approved_ot():
    if REQUIRE_CONFIRM:
        status_to_test = CONFIRMED
    else:
        status_to_test = APPROVED

    to_process = PreApprovalOvertime.objects.filter(
        status=status_to_test,
        overtime_entry__isnull=True
    )
    overtime_entries_created = list()

    not_present = no_punch_out = no_timesheet = no_setting = 0
    for pre_approval in to_process:
        time_sheet = TimeSheet.objects.filter(
            timesheet_for=pre_approval.overtime_date,
            timesheet_user=pre_approval.sender
        ).first()
        pre_approval_setting = pre_approval.sender.attendance_setting.overtime_setting
        if not pre_approval_setting:
            logger.debug(f"{pre_approval} overtime setting not found.")
            no_setting += 1
            continue
        if not time_sheet:
            logger.debug(f"{pre_approval} candidate timesheet not found.")
            no_timesheet += 1
            continue
        if not time_sheet.is_present:
            logger.debug(f"{pre_approval} candidate timesheet was not present.")
            not_present += 1
            continue
        if not time_sheet.punch_out:
            logger.debug(f"{pre_approval} candidate timesheet is incomplete and was'nt processed.")
            no_punch_out += 1
            continue

        overtime_duration = get_hours_for_pre_approved_overtime(pre_approval, pre_approval_setting,
                                                                time_sheet)
        entry = OvertimeEntry(
            user=pre_approval.sender,
            overtime_settings=pre_approval_setting,
            timesheet=time_sheet
        )
        entry.save()
        overtime_entries_created.append(entry)
        overtime_entry_detail = dict(
            punch_in_overtime=timedelta(0),
            punch_out_overtime=overtime_duration,
            overtime_entry=entry
        )
        ot_detail = OvertimeEntryDetail.objects.create(**overtime_entry_detail)
        ot_detail.claimed_overtime = timedelta(
            seconds=ot_detail.total_seconds
        )
        ot_detail.normalized_overtime = timedelta(
            seconds=ot_detail.normalized_overtime_seconds
        )
        ot_detail.save()
        generate_overtime_claim_for_pre_approved_ot(
            entry,
            pre_approval,
            pre_approval_setting
        )
        pre_approval.overtime_entry = entry
        pre_approval.save(update_fields=['overtime_entry'])
    statistics = {
        'Total Processed': to_process.count(),
        'not_present': not_present,
        'no_punch_out': no_punch_out,
        'no_timesheet': no_timesheet,
        'no_setting': no_setting,
    }
    generate_overtime_notification(overtime_entries_created, pre_approval=True)
    return statistics


def get_hours_for_pre_approved_overtime(pre_approval, pre_approval_setting, time_sheet):
    overtime_duration = pre_approval.overtime_duration
    early, late = get_early_late_overtime(
        time_sheet,
        pre_approval_setting
    )
    earned_overtime = early + late
    if earned_overtime <= overtime_duration and (
        pre_approval_setting.reduce_ot_if_actual_ot_lt_approved_ot
    ):
        overtime_duration = earned_overtime
    elif earned_overtime > overtime_duration and (
        pre_approval_setting.actual_ot_if_actual_gt_approved_ot
    ):
        overtime_duration = earned_overtime
    return overtime_duration


def is_pre_approved_overtime_editable(pre_approval):
    """If OT Claim belonging to Pre Approval is confirmed, block!"""
    setting_allows = nested_getattr(
        pre_approval.sender,
        'attendance_setting.overtime_setting.allow_edit_of_pre_approved_overtime'
    )
    is_ot_confirmed = nested_getattr(pre_approval, 'overtime_entry.claim.status') == CONFIRMED
    return setting_allows and not is_ot_confirmed


def recalibrate_overtime_claim_when_pre_approval_is_modified(pre_approval):
    if not is_pre_approved_overtime_editable(pre_approval):
        return
    # catch a signal or link through serializer.
    overtime_entry = pre_approval.overtime_entry
    if not overtime_entry:
        # no need to re-calibrate.
        return
    overtime_duration = pre_approval.overtime_duration
    pre_approval_setting = overtime_entry.overtime_settings
    if pre_approval_setting.reduce_ot_if_actual_ot_lt_approved_ot:
        early, late = get_early_late_overtime(
            overtime_entry.timesheet,
            pre_approval_setting
        )
        overtime_duration = min(
            (
                overtime_duration, (early + late)
            )
        )
    detail = overtime_entry.overtime_detail
    old_ot = detail.punch_out_overtime
    if old_ot == overtime_duration:
        return
    detail.punch_out_overtime = overtime_duration
    detail.claimed_overtime = timedelta(
        seconds=detail.total_seconds
    )
    detail.normalized_overtime = timedelta(
        seconds=detail.normalized_overtime_seconds
    )
    detail.save()
    detail.histories.create(
        actor=get_system_admin(),
        previous_punch_in_overtime=timedelta(0),
        previous_punch_out_overtime=old_ot,
        current_punch_in_overtime=timedelta(0),
        current_punch_out_overtime=overtime_duration,
        remarks='Re-calibrated after Pre Approval modification.'
    )
    overtime_claim_frontend = "/user/attendance/reports/overtime-claims"
    recipient = pre_approval.sender
    ws_remark = 'Your overtime claim for {} has been re-calibrated'.format(
        pre_approval.overtime_date
    )
    add_notification(
        actor=get_system_admin(),
        text=ws_remark,
        recipient=recipient,
        action=pre_approval,
        url=overtime_claim_frontend
    )
