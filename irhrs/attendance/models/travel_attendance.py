from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models

from irhrs.attendance.constants import TRAVEL_ATTENDANCE_STATUS_CHOICES, \
    TRAVEL_ATTENDANCE_PART_CHOICES, FULL_DAY
from irhrs.attendance.models import TimeSheet
from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_upload_path
from irhrs.organization.models import Organization

USER = get_user_model()


class TravelAttendanceSetting(BaseModel):
    organization = models.OneToOneField(
        to=Organization,
        on_delete=models.CASCADE,
        related_name='travel_setting'
    )
    can_apply_in_offday = models.BooleanField()
    can_apply_in_holiday = models.BooleanField()

    def __str__(self):
        return (
            str(self.organization)
            + ' [x] Offday' if self.can_apply_in_offday else ' [ ] Offday'
                                                             + ' [x] Holiday' if self.can_apply_in_holiday else ' [ ] Holiday'
        )


class TravelAttendanceRequest(BaseModel):
    user = models.ForeignKey(
        to=USER,
        related_name='travel_requests',
        on_delete=models.CASCADE
    )
    location = models.CharField(max_length=255, default='')
    start = models.DateField()
    start_time = models.TimeField()
    end = models.DateField()
    end_time = models.TimeField()
    working_time = models.CharField(
        choices=TRAVEL_ATTENDANCE_PART_CHOICES,
        max_length=20,
        default=FULL_DAY,
        help_text='If the user decides to work first half, second half, or full time.',
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=TRAVEL_ATTENDANCE_STATUS_CHOICES,
        help_text='Status of this travel request.',
        db_index=True
    )
    request_remarks = models.CharField(
        max_length=255
    )
    action_remarks = models.CharField(
        max_length=255
    )
    recipient = models.ForeignKey(
        to=USER,
        related_name='travel_attendance_requests',
        on_delete=models.CASCADE
    )
    balance = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{str(self.id).rjust(4, '0')} {self.user} {self.status}"

    def history_logs(self):
        return self.histories.order_by('created_at').all()


class TravelAttendanceRequestHistory(BaseModel):
    travel_attendance = models.ForeignKey(
        to=TravelAttendanceRequest,
        related_name='histories',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20,
        choices=TRAVEL_ATTENDANCE_STATUS_CHOICES,
        help_text='Status of this travel request.',
        db_index=True
    )
    remarks = models.CharField(
        max_length=255
    )
    action_performed_to = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.travel_attendance) + self.get_status_display()


class TravelAttendanceDays(BaseModel):
    travel_attendance = models.ForeignKey(
        to=TravelAttendanceRequest,
        related_name='travel_attendances',
        on_delete=models.CASCADE
    )
    day = models.DateField()
    is_archived = models.BooleanField(default=False)
    # Because there can be multiple timesheets for a day.
    timesheets = models.ManyToManyField(
        to=TimeSheet,
    )
    user = models.ForeignKey(
        to=USER,
        related_name='travel_attendance_days',
        on_delete=models.CASCADE
    )
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = 'created_at',

    def __str__(self):
        return f"{self.travel_attendance} {self.day.isoformat()} "


class TravelAttendanceAttachments(models.Model):
    travel_request = models.ForeignKey(
        to=TravelAttendanceRequest,
        related_name='attachments',
        on_delete=models.CASCADE
    )
    file = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
        )]
    )
    filename = models.CharField(max_length=255)

    class Meta:
        ordering = 'filename',


class TravelAttendanceDeleteRequest(BaseModel):
    travel_attendance = models.ForeignKey(
        to=TravelAttendanceRequest,
        on_delete=models.CASCADE,
        related_name='delete_request'
    )
    recipient = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )
    request_remarks = models.CharField(
        max_length=255
    )
    action_remarks = models.CharField(
        max_length=255
    )
    status = models.CharField(
        max_length=20,
        choices=TRAVEL_ATTENDANCE_STATUS_CHOICES,
        help_text='Status of this travel request.',
        db_index=True
    )
    deleted_days = models.ManyToManyField(
        to=TravelAttendanceDays
    )

    def __str__(self):
        return 'Delete Request: ' + str(self.travel_attendance)

    @property
    def histories(self):
        return self.history.order_by('created_at').all()


class TravelAttendanceDeleteRequestHistory(BaseModel):
    delete_request = models.ForeignKey(
        to=TravelAttendanceDeleteRequest,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action_performed_to = models.ForeignKey(
        to=USER,
        related_name='+',
        on_delete=models.CASCADE
    )
    action_performed = models.CharField(
        max_length=20,
        choices=TRAVEL_ATTENDANCE_STATUS_CHOICES,
        help_text='Status of this travel request.',
        db_index=True
    )
    remarks = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.created_by} {self.action_performed} to {self.action_performed_to}"
