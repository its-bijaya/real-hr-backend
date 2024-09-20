from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.constants.payroll import UNIT_OF_WORK_REQUEST_STATUS_CHOICES, REQUESTED, CANCELED, \
    APPROVED, DENIED, CONFIRMED, FORWARDED
from irhrs.core.utils.common import get_upload_path
from irhrs.payroll.models import OperationRate

USER = get_user_model()


class UnitOfWorkRequest(BaseModel):
    user = models.ForeignKey(
        to=USER,
        on_delete=models.CASCADE,
        related_name='unit_of_work_requests'
    )
    recipient = models.ForeignKey(
        to=USER,
        on_delete=models.CASCADE,
        related_name='received_unit_of_work_requests'
    )

    rate = models.ForeignKey(
        to=OperationRate,
        on_delete=models.CASCADE,
        related_name='unit_of_work_requests'
    )
    quantity = models.FloatField(default=0)

    status = models.CharField(choices=UNIT_OF_WORK_REQUEST_STATUS_CHOICES,
                              default=REQUESTED, max_length=25, db_index=True)

    attachment = models.FileField(
        upload_to=get_upload_path,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)]
    )
    remarks = models.TextField(max_length=600)

    confirmed_on = models.DateField(null=True)

    def __str__(self):
        return f"Unit of work Request of {self.user}: {self.rate} "


class UnitOfWorkRequestHistory(BaseModel):
    request = models.ForeignKey(
        UnitOfWorkRequest, related_name='histories',
        on_delete=models.CASCADE
    )
    action_performed = models.CharField(
        choices=UNIT_OF_WORK_REQUEST_STATUS_CHOICES,
        max_length=25,
    )
    action_performed_by = models.ForeignKey(
        to=USER, related_name='acted_unit_of_work', on_delete=models.CASCADE
    )
    action_performed_to = models.ForeignKey(
        to=USER, related_name='requested_unit_of_work_histories',
        on_delete=models.SET_NULL, null=True
    )
    remark = models.CharField(max_length=255, blank=True)

    def __str__(self):
        if self.action_performed in [REQUESTED, CANCELED]:
            return f"{self.action_performed_by} {self.action_performed.lower()}" \
                   f" unit of work with remarks '{self.remark}'"
        if self.action_performed in [APPROVED, DENIED, CONFIRMED]:
            return f"{self.action_performed_by} {self.action_performed.lower()}" \
                   f" {self.request.user.full_name}'s unit of work request with " \
                   f"remarks '{self.remark}'"
        if self.action_performed == FORWARDED:
            return f"{self.action_performed_by} {self.action_performed.lower()}" \
                   f" {self.request.user.full_name}'s unit of work request to" \
                   f" {self.action_performed_to} with " \
                   f"remarks '{self.remark}'"
        return "Undefined action performed."

    class Meta:
        ordering = ('created_at',)
