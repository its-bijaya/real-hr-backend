from itertools import chain

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_upload_path
from irhrs.leave.constants.model_constants import LEAVE_REQUEST_STATUS, \
    REQUESTED, HALF_LEAVE_CHOICES, LEAVE_REQUEST_DELETE_STATUS, FULL_DAY, RECIPIENT_TYPE, \
    SUPERVISOR
from irhrs.leave.managers.setting import LeaveRequestManager
from irhrs.leave.models import LeaveRule, LeaveAccount

User = get_user_model()


class LeaveRequest(BaseModel):

    user = models.ForeignKey(
        User,
        related_name='leave_requests',
        on_delete=models.CASCADE,
        # User who makes request for leave
    )
    recipient = models.ForeignKey(
        User,
        related_name='received_leave_requests',
        null=True,
        on_delete=models.SET_NULL,
        # User who acts on this leave request
    )
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_TYPE, default=SUPERVISOR,
                                      db_index=True)
    leave_rule = models.ForeignKey(
        LeaveRule,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_account = models.ForeignKey(
        LeaveAccount,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    start = models.DateTimeField()
    end = models.DateTimeField()

    status = models.CharField(
        max_length=10,
        choices=LEAVE_REQUEST_STATUS,
        default=REQUESTED,
        db_index=True
    )

    details = models.TextField(max_length=600)

    # the balance consumed by this leave request
    balance = models.FloatField(null=True)

    is_archived = models.BooleanField(default=False)  # after account expires
    is_deleted = models.BooleanField(default=False) # after leave deleted.

    part_of_day = models.CharField(
        max_length=10,
        choices=HALF_LEAVE_CHOICES,
        blank=True,
        db_index=True
    )

    attachment = models.FileField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )

    objects = LeaveRequestManager()

    def __str__(self):
        if self.part_of_day == FULL_DAY:
            if self.start.date() == self.start.date():
                return f"{self.get_part_of_day_display()} " \
                       f"{self.user} {self.start.date()}"
            return f"{self.get_part_of_day_display()} " \
                   f"{self.user} ({self.start.date()}-{self.end.date()}"
        return f"{self.get_part_of_day_display()} {self.user} {self.start.date()}"


class LeaveRequestHistory(BaseModel):
    request = models.ForeignKey(
        LeaveRequest,
        related_name="history",
        on_delete=models.CASCADE
    )
    action = models.CharField(
        choices=LEAVE_REQUEST_STATUS,
        max_length=10,
        db_index=True
    )
    actor = models.ForeignKey(
        User,
        related_name="acted_leave_requests",
        on_delete=models.SET_NULL,
        null=True
    )
    forwarded_to = models.ForeignKey(
        User,
        related_name="forwarded_leave_requests",
        on_delete=models.SET_NULL,
        null=True
    )
    remarks = models.TextField(blank=True)
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_TYPE, default=SUPERVISOR,
                                      db_index=True)

    def __str__(self):
        return f"{self.actor} {self.action} {self.request}"


class LeaveRequestDeleteHistory(BaseModel):
    leave_request = models.ForeignKey(
        to=LeaveRequest,
        on_delete=models.CASCADE,
        related_name='delete_history'
    )
    recipient = models.ForeignKey(
        User,
        related_name='delete_history',
        on_delete=models.SET_NULL,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=LEAVE_REQUEST_DELETE_STATUS,
        default=REQUESTED,
        db_index=True
    )
    remarks = models.CharField(
        max_length=255
    )

    def __str__(self):
        return f"{self.get_status_display()} cancellation {self.leave_request}"


class LeaveRequestDeleteStatusHistory(BaseModel):
    delete_history = models.ForeignKey(
        to=LeaveRequestDeleteHistory,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    status = models.CharField(
        max_length=20,
        choices=LEAVE_REQUEST_DELETE_STATUS,
        default=REQUESTED,
        db_index=True
    )
    remarks = models.CharField(
        max_length=255
    )

    def __str__(self):
        return f"{self.get_status_display()} of {self.delete_history}"


class LeaveSheet(BaseModel):
    """
    Store balance distribution for each leave day for a leave request

    :cvar request: leave request
    :cvar leave_for: date for which leave is applied
    :cvar balance: balance deduced for that day
    :cvar balance_minutes: balance for hourly leave categories.

    :cvar start: timestamp when leave will be applicable from
    :cvar end: timestamp till when leave for `leave_for` will be valid till

    """
    request = models.ForeignKey(
        LeaveRequest,
        related_name="sheets",
        on_delete=models.CASCADE
    )
    leave_for = models.DateField()
    balance = models.FloatField()
    balance_minutes = models.FloatField(null=True)

    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return "{} between {} and {} for {}".format(
            (
                f"{self.balance} days" if self.balance else
                f"{self.balance_minutes} minutes"
            ),
            self.start,
            self.end,
            self.request
        )


class HourlyLeavePerDay(BaseModel):
    """
    This model keeps aggregate of hourly leave per day grouped by is_paid flag.
    """
    user = models.ForeignKey(User, related_name='hourly_leaves_per_day', on_delete=models.CASCADE)
    leave_for = models.DateField()
    is_paid = models.BooleanField()
    balance = models.FloatField(validators=[MinValueValidator(limit_value=0)],
                                help_text="Unit is days.")

    class Meta:
        unique_together = ('user', 'leave_for', 'is_paid')

    def __str__(self):
        return f"{self.balance} day Hourly Leave" \
               f" ({('Unpaid', 'Paid')[self.is_paid]}) on {self.leave_for} by {self.user}"



